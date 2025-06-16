import hashlib
import io
from pathlib import Path
from typing import Any

from fastapi import Depends, HTTPException
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.schemas.book_schemas import BookInDB, BookUpdate
from core.config import settings
from core.crockford import generate_crockford_id
from core.logger import logger
from database import book_crud, get_database
from database.storage_crud import get_default_storage
from models.user import User
from parsers.base_parser import BookParser
from parsers.epub_parser import EpubParser
from parsers.pdf_parser import PdfParser
from services.exceptions import StorageBackendError
from services.filesystem_storage import FileSystemStorage
from services.minio_storage import MinIOStorage
from services.storage_backend import StorageBackend, StorageFileType

PARSER_MAPPING = {
    "EPUB": EpubParser,
    "PDF": PdfParser,
}

STORAGE_BACKENDS = {
    "FILE_SYSTEM": FileSystemStorage,
    "MINIO": MinIOStorage,
}


class BookService:
    def __init__(self, db: AsyncSession = Depends(get_database)):
        self.db = db

    def _generate_file_hash(self, file_path: Path, hash_algo="md5") -> str:
        hasher = hashlib.new(hash_algo)

        with file_path.open("rb") as file:
            for chunk in iter(lambda: file.read(4096), b""):
                hasher.update(chunk)

        return hasher.hexdigest()

    async def _get_parser(self, file_path: Path) -> BookParser | None:
        file_format = BookParser.get_file_format(file_path)

        if not file_format:
            logger.error(f"Could not determine file format for {file_path}.")
            return None

        parser = PARSER_MAPPING.get(file_format)

        if parser:
            return parser()

        return None

    async def _process_cover(
        self,
        user: User,
        filename: str,
        cover: bytes,
    ) -> list[dict[str, Any]]:
        covers = []
        storage_backend = await self.get_storage_backend(user)

        try:
            image = Image.open(io.BytesIO(cover))
        except Exception:
            logger.exception(f"Error opening cover image for {filename}.")
            return covers

        variants = [
            {
                "name": "original",
                "size": None,
                "quality": 100,
            },
            {
                "name": "thumbnail",
                "size": (150, 200),
                "quality": 80,
            },
        ]

        for variant in variants:
            try:
                variant_image = image.copy()

                if variant["size"]:
                    variant_image.thumbnail(variant["size"])

                cover_filename = f"{filename}_cover_{variant['name']}.jpg"
                cover_path_temp = settings.TEMP_FILES_DIR / cover_filename

                variant_image.convert("RGB").save(
                    cover_path_temp,
                    "JPEG",
                    quality=variant["quality"],
                )

                cover_path_real = storage_backend.store_file(
                    user,
                    cover_path_temp,
                    cover_filename,
                    StorageFileType.COVER,
                )

                covers.append(
                    {
                        "filename": cover_filename,
                        "path": str(cover_path_real),
                        "variant": variant["name"],
                    },
                )
            except Exception:
                logger.exception(
                    f"Error processing cover variant '{variant['name']}' for {filename}.",
                )

        for cover_file in covers:
            cover_path_temp = settings.TEMP_FILES_DIR / cover_file["filename"]

            if cover_path_temp.exists():
                cover_path_temp.unlink()

        return covers

    async def get_storage_backend(self, user: User | None) -> StorageBackend:
        if not user:
            raise HTTPException(
                status_code=401,
                detail="User not authenticated.",
            )

        user_id = user.id
        # Crockford IDs are strings, so no need to check for int
        storage = await get_default_storage(self.db, user_id)

        if not storage:
            return STORAGE_BACKENDS["FILE_SYSTEM"]()

        match storage.storage_type:
            case "FILE_SYSTEM":
                return STORAGE_BACKENDS["FILE_SYSTEM"]()
            case "MINIO":
                config = storage.config

                return STORAGE_BACKENDS["MINIO"](
                    access_key=config["access_key"],
                    secret_key=config["secret_key"],
                    endpoint=config["endpoint"],
                    bucket_name=config["bucket_name"],
                    secure=config.get("secure", False),
                )
            case _:
                raise StorageBackendError(StorageBackendError.NOT_FOUND)

    async def store_book(
        self,
        source_path: Path,
        original_filename: str,
        user: User | None = None,
    ) -> BookInDB | None:
        file_hash = self._generate_file_hash(source_path)
        existing_book = await book_crud.get_book_by_hash(self.db, file_hash)

        if existing_book:
            if source_path.exists():
                source_path.unlink()

            logger.warning(
                f"Book with same content (hash: {file_hash}) already exists with ID: {getattr(existing_book, 'id', None)}.",
            )

            return None

        parser = await self._get_parser(source_path)

        if not parser:
            if source_path.exists():
                source_path.unlink()

            logger.warning(f"Unsupported file format for {original_filename}.")
            return None

        metadata = parser.parse_metadata(source_path)

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
                parser.get_file_format(source_path),
            ),
            "file_hash": file_hash,
            "file_size_bytes": source_path.stat().st_size,
            "original_filename": original_filename,
        }

        book_data = {k: v for k, v in book_data.items() if v is not None}

        book_data["id"] = generate_crockford_id()

        try:
            storage_backend = await self.get_storage_backend(user)
        except (StorageBackendError, KeyError) as error:
            logger.exception("Error getting storage backend.")

            raise HTTPException(
                status_code=400,
                detail="Failed to acquire storage backend.",
            ) from error
        except Exception as error:
            logger.exception("Unexpected error while getting storage backend.")

            raise HTTPException(
                status_code=500,
                detail="Unexpected error while getting storage backend.",
            ) from error

        stored_filename = f"{source_path.stem}{source_path.suffix}"

        stored_file_path = storage_backend.store_file(
            user,
            source_path,
            stored_filename,
            StorageFileType.BOOK,
        )

        book_data["stored_filename"] = stored_filename
        book_data["file_path"] = str(stored_file_path)
        cover_data_tuple = parser.extract_cover_image_data(source_path)

        if cover_data_tuple:
            book_data["covers"] = await self._process_cover(
                user,
                source_path.stem,
                cover_data_tuple[0],
            )

        created_book = await book_crud.create_book_metadata(self.db, book_data)

        if source_path.exists():
            source_path.unlink()

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

    async def get_book_by_id(self, book_id: str):
        book = await book_crud.get_book_by_id(self.db, book_id)

        if not book:
            raise HTTPException(status_code=404, detail="Book not found.")

        return BookInDB.model_validate(book.__dict__)

    async def update_book_by_id(
        self,
        book_id: str,
        book_update_data: BookUpdate,
    ) -> dict[str, Any] | None:
        return await book_crud.update_book_metadata(self.db, book_id, book_update_data)

    async def delete_book_by_id(self, user: User, book_id: str) -> int:
        book = await book_crud.get_book_by_id(self.db, book_id)

        if not book:
            return 0

        try:
            storage_backend = await self.get_storage_backend(user)
        except (StorageBackendError, KeyError):
            logger.exception("Error getting storage backend.")
            return 0

        if book.stored_filename:
            storage_backend.delete_file(
                user,
                book.stored_filename,
                StorageFileType.BOOK,
            )

        for cover in book.covers:
            storage_backend.delete_file(
                user,
                cover["filename"],
                StorageFileType.COVER,
            )

        return await book_crud.delete_book_metadata(self.db, book_id)


def get_book_service(
    database: AsyncSession = Depends(get_database),
) -> BookService:
    return BookService(database)
