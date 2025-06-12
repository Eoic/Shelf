from ast import In
import hashlib
import io
import mimetypes
from pathlib import Path
from typing import Any, Optional
import uuid

from fastapi import Depends, HTTPException
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.schemas.book_schemas import BookInDB, BookUpdate
from core.config import settings
from core.logger import logger
from database import book_crud, get_database
from models.user import User
from parsers.base_parser import BookParser
from parsers.epub_parser import EpubParser
from parsers.pdf_parser import PdfParser
from services.filesystem_storage import FileSystemStorage
from services.minio_storage import MinIOStorage
from services.storage_backend import StorageBackend

PARSER_MAPPING = {
    "EPUB": EpubParser,
    "PDF": PdfParser,
}

STORAGE_BACKENDS = {
    "filesystem": FileSystemStorage,
    "minio": MinIOStorage,
}


class InvalidStorageBackendError(Exception):
    MINIO_NOT_CONFIGURED = "MinIO credentials not configured in user preferences."
    STORAGE_NOT_FOUND = "Specified storage backend not found."

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class BookService:
    def __init__(self, db: AsyncSession = Depends(get_database)):
        self.db = db

    async def _get_user_storage_backend(self, user: User | None) -> StorageBackend:
        if not user or not hasattr(user, "preferences"):
            raise HTTPException(
                status_code=400,
                detail="User preferences not found. Ensure user is authenticated.",
            )

        backend = user.preferences.get("storage_backend")

        match backend:
            case "filesystem":
                return STORAGE_BACKENDS["filesystem"]()
            case "minio":
                if not user.preferences.get("minio_credentials"):
                    raise InvalidStorageBackendError(
                        InvalidStorageBackendError.MINIO_NOT_CONFIGURED,
                    )

                credentials = user.preferences["minio_credentials"]

                return STORAGE_BACKENDS["minio"](
                    access_key=credentials["access_key"],
                    secret_key=credentials["secret_key"],
                    endpoint=credentials["endpoint"],
                    secure=credentials.get("secure", False),
                )
            case _:
                raise InvalidStorageBackendError(
                    InvalidStorageBackendError.STORAGE_NOT_FOUND,
                )

    async def _get_parser(self, file_path: Path) -> BookParser | None:
        file_format = BookParser.get_file_format(file_path)

        if not file_format:
            logger.error(f"Could not determine file format for {file_path}.")
            return None

        parser = PARSER_MAPPING.get(file_format)

        if parser:
            return parser()

        return None

    def _generate_file_hash(self, file_path: Path, hash_algo="md5") -> str:
        hasher = hashlib.new(hash_algo)

        with file_path.open("rb") as file:
            for chunk in iter(lambda: file.read(4096), b""):
                hasher.update(chunk)

        return hasher.hexdigest()

    async def store_book(
        self,
        file_path: Path,
        original_filename: str,
        user: User | None = None,
    ) -> BookInDB | None:
        file_hash = self._generate_file_hash(file_path)
        existing_book = await book_crud.get_book_by_hash(self.db, file_hash)

        if existing_book:
            if file_path.exists():
                file_path.unlink()

            logger.warning(
                f"Book with same content (hash: {file_hash}) already exists with ID: {getattr(existing_book, 'id', None)}.",
            )

            return None

        parser = await self._get_parser(file_path)

        if not parser:
            if file_path.exists():
                file_path.unlink()

            logger.warning(f"Unsupported file format for {original_filename}.")
            return None

        metadata = parser.parse_metadata(file_path)

        if "parsing_error" in metadata:
            logger.warning(
                f"Metadata parsing issue for {original_filename}: {metadata['parsing_error']}",
            )

        book_data: dict[str, Any] = {
            "title": metadata.get("title") or original_filename,
            "authors": metadata.get("authors", []),
            "publisher": metadata.get("publisher"),
            "publication_date": metadata.get("publication_date"),
            "language": metadata.get("language"),
            "description": metadata.get("description"),
            "tags": metadata.get("tags", []),
            "identifiers": metadata.get("identifiers", []),
            "format": metadata.get(
                "format",
                parser.get_file_format(file_path),
            ),
            "file_hash": file_hash,
            "file_size_bytes": file_path.stat().st_size,
            "original_filename": original_filename,
        }

        book_data = {k: v for k, v in book_data.items() if v is not None}
        filename_stem = str(uuid.uuid4())
        filename_ext = file_path.suffix

        try:
            storage_backend = await self._get_user_storage_backend(user)
        except (InvalidStorageBackendError, KeyError) as error:
            logger.exception("Error getting storage backend.")

            raise HTTPException(
                status_code=400,
                detail="Invalid storage backend configuration.",
            ) from error

        stored_filename = f"{filename_stem}{filename_ext}"
        stored_file_path = storage_backend.store_file(file_path, stored_filename)

        book_data["file_path"] = stored_file_path
        cover_filename = None
        cover_data_tuple = parser.extract_cover_image_data(Path(stored_file_path))

        if cover_data_tuple:
            image_bytes, _original_mimetype = cover_data_tuple

            try:
                image = Image.open(io.BytesIO(image_bytes))
                cover_filename_main = f"{filename_stem}_cover.jpg"
                cover_path_main = settings.COVER_FILES_DIR / cover_filename_main
                image.convert("RGB").save(cover_path_main, "JPEG", quality=100)
                thumbnail_filename = f"{filename_stem}_cover_thumbnail.jpg"
                thumbnail_path = settings.COVER_FILES_DIR / thumbnail_filename
                image.thumbnail((150, 200))
                image.convert("RGB").save(thumbnail_path, "JPEG", quality=100)
                cover_filename = cover_filename_main
            except Exception as error:
                logger.error(
                    f"Could not process/save cover for {original_filename}: {error}",
                )

        if cover_filename:
            book_data["cover_filename"] = cover_filename

        created_book = await book_crud.create_book_metadata(self.db, book_data)

        return BookInDB.model_validate(created_book)

    async def get_books(
        self,
        skip: int,
        limit: int,
        search_query: str | None,
    ) -> tuple[list[dict[str, Any]], int]:
        books, count = await book_crud.get_all_books(self.db, skip, limit, search_query)

        return [
            BookInDB.model_validate(book.__dict__).model_dump() for book in books
        ], int(count or 0)

    async def get_book_by_id(self, book_id: int):
        book = await book_crud.get_book_by_id(self.db, book_id)

        if not book:
            raise HTTPException(status_code=404, detail="Book not found.")

        return BookInDB.model_validate(book.__dict__)

    async def update_book_by_id(
        self,
        book_id: int,
        book_update_data: BookUpdate,
    ) -> dict[str, Any] | None:
        return await book_crud.update_book_metadata(self.db, book_id, book_update_data)

    async def delete_book_by_id(self, book_id: int) -> int:
        book_to_delete = await book_crud.get_book_by_id(self.db, book_id)

        if not book_to_delete:
            return 0

        file_path = getattr(book_to_delete, "file_path", None)

        if file_path and isinstance(file_path, str):
            file_to_delete = Path(file_path)

            if file_to_delete.exists():
                file_to_delete.unlink()

        cover_filename = getattr(book_to_delete, "cover_filename", None)

        if cover_filename and isinstance(cover_filename, str):
            cover_to_delete = settings.COVER_FILES_DIR / cover_filename

            if cover_to_delete.exists():
                cover_to_delete.unlink()

        return await book_crud.delete_book_metadata(self.db, book_id)

    async def get_book_cover_path(self, book_id: int) -> tuple[Path | None, str | None]:
        book = await self.get_book_by_id(book_id)

        if book and book.cover_filename:
            cover_path = settings.COVER_FILES_DIR / book.cover_filename

            if cover_path.exists():
                media_type, _ = mimetypes.guess_type(cover_path)
                return cover_path, media_type or "image/jpeg"

        return None, None

    async def get_book_file_path(
        self,
        book_id: int,
    ) -> tuple[Path | None, str | None, str | None]:
        book = await self.get_book_by_id(book_id)

        if book and book.original_filename and book.format:
            file_path = settings.BOOK_FILES_DIR / book.original_filename

            if file_path.exists():
                media_type, _ = mimetypes.guess_type(file_path)

                match book.format:
                    case "EPUB":
                        media_type = media_type or "application/epub+zip"
                    case "PDF":
                        media_type = media_type or "application/pdf"
                    case format if format and format.startswith("MOBI"):
                        media_type = media_type or "application/x-mobipocket-book"

                return (
                    file_path,
                    book.original_filename or "book_file",
                    media_type,
                )

        return None, None, None


def get_book_service(
    database: AsyncSession = Depends(get_database),
) -> BookService:
    return BookService(database)
