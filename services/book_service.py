import hashlib
import io
from pathlib import Path
from typing import Any

from fastapi import Depends, HTTPException
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.schemas.book_schemas import BookInDB, BookUpdate
from core.crockford import generate_crockford_id
from core.logger import logger
from database import async_session, book_crud, get_database
from database.storage_crud import get_default_storage
from models.book import Book
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
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    async def create_queued_book(
        original_filename: str,
        user_id: str | None,
        temp_file_path: Path,
    ) -> str:
        async with async_session() as db:
            book_id = generate_crockford_id()
            book = Book(
                id=book_id,
                title=original_filename,
                original_filename=original_filename,
                status="queued",
                covers=[],
                file_path=str(temp_file_path),
            )
            db.add(book)
            await db.commit()
            await db.refresh(book)
            return book_id

    async def update_book_status(
        self,
        book_id: str,
        status: str,
        error: str | None = None,
    ):
        book = await book_crud.get_book_by_id(self.db, book_id)

        if book:
            book.status = status
            book.processing_error = error
            await self.db.commit()
            await self.db.refresh(book)

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
        book_hash: str,
        book_temp_path: Path,
        cover: bytes,
    ) -> list[dict[str, Any]]:
        covers = []
        storage_backend = await self.get_storage_backend(user)

        try:
            image = Image.open(io.BytesIO(cover))
        except Exception:
            logger.exception(f"Error opening cover image for {book_hash}.")
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

                cover_filename = f"{variant['name']}.jpg"

                variant_image.convert("RGB").save(
                    book_temp_path.parent / cover_filename,
                    "JPEG",
                    quality=variant["quality"],
                )

                cover_path_real = storage_backend.store_file(
                    user,
                    book_temp_path.parent / cover_filename,
                    book_hash,
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
                    f"Error processing cover variant '{variant['name']}' for {book_hash}.",
                )

        for cover_file in covers:
            cover_path_temp = book_temp_path.parent / cover_file["filename"]

            if cover_path_temp.exists():
                cover_path_temp.unlink()

        return covers

    async def get_storage_backend(self, user: User | str | None) -> StorageBackend:
        if not user:
            raise HTTPException(
                status_code=401,
                detail="User not authenticated.",
            )

        if isinstance(user, str):
            user_obj = await self.db.get(User, user)

            if not user_obj:
                raise HTTPException(status_code=404, detail="User not found.")

            user = user_obj

        user_id = user.id
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

    @staticmethod
    async def store_book(
        source_file_path: Path,
        original_filename: str,
        user_id: str | None = None,
        book_id: str | None = None,
    ) -> BookInDB | None:
        from database import async_session
        from models.user import User

        async with async_session() as db:
            if book_id is None:
                book_id = generate_crockford_id()

            user = None

            if user_id:
                user = await db.get(User, user_id)

            service = BookService(db)
            return await service._store_book_impl(
                source_file_path,
                original_filename,
                book_id,
                user,
            )

    async def _store_book_impl(
        self,
        source_file_path: Path,
        original_filename: str,
        book_id,
        user: User | None = None,
    ) -> BookInDB | None:
        await self.update_book_status(book_id, "processing")

        try:
            file_hash = self._generate_file_hash(source_file_path)
            existing_book = await book_crud.get_book_by_hash(self.db, file_hash)

            if existing_book:
                if source_file_path.exists():
                    source_file_path.unlink()

                await self.update_book_status(book_id, "failed", error="Duplicate book")

                logger.warning(
                    f"Book with same content (hash: {file_hash}) already exists with ID: {getattr(existing_book, 'id', None)}.",
                )
                return None

            parser = await self._get_parser(source_file_path)

            if not parser:
                if source_file_path.exists():
                    source_file_path.unlink()

                await self.update_book_status(
                    book_id,
                    "failed",
                    error="Unsupported file format",
                )

                logger.warning(f"Unsupported file format for {original_filename}.")
                return None

            metadata = parser.parse_metadata(source_file_path)

            if "parsing_error" in metadata:
                logger.warning(
                    f"Metadata parsing issue for {original_filename}: {metadata['parsing_error']}",
                )

            book_data: dict[str, Any] = {
                # "id": book_id,
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
                    parser.get_file_format(source_file_path),
                ),
                "file_hash": file_hash,
                "file_size_bytes": source_file_path.stat().st_size,
                "original_filename": original_filename,
                "status": "processing",
                "covers": [],
            }

            book_data = {k: v for k, v in book_data.items() if v is not None}

            try:
                storage_backend = await self.get_storage_backend(user)
            except (StorageBackendError, KeyError) as error:
                logger.exception("Error getting storage backend.")

                await self.update_book_status(
                    book_id,
                    "failed",
                    error="Failed to acquire storage backend.",
                )

                raise HTTPException(
                    status_code=400,
                    detail="Failed to acquire storage backend.",
                ) from error
            except Exception as error:
                logger.exception("Unexpected error while getting storage backend.")

                await self.update_book_status(
                    book_id,
                    "failed",
                    error="Unexpected error while getting storage backend.",
                )
                raise HTTPException(
                    status_code=500,
                    detail="Unexpected error while getting storage backend.",
                ) from error

            stored_filename = f"{source_file_path.stem}{source_file_path.suffix}"

            stored_file_path = storage_backend.store_file(
                user,
                source_file_path,
                file_hash,
                stored_filename,
                StorageFileType.BOOK,
            )

            book_data["stored_filename"] = stored_filename
            book_data["file_path"] = str(stored_file_path)
            cover_data_tuple = parser.extract_cover_image_data(source_file_path)

            if cover_data_tuple:
                book_data["covers"] = await self._process_cover(
                    user,
                    file_hash,
                    source_file_path,
                    cover_data_tuple[0],
                )

            await book_crud.update_book_metadata(
                self.db,
                book_id,
                BookUpdate(**book_data),
            )

            await self.update_book_status(book_id, "completed")

            if source_file_path.exists():
                source_file_path.unlink()

            book = await book_crud.get_book_by_id(self.db, book_id)
            return BookInDB.model_validate(book.__dict__)
        except Exception as e:
            await self.update_book_status(book_id, "failed", error=str(e))
            logger.exception(f"Book processing failed for {original_filename}: {e}")

            if source_file_path.exists():
                source_file_path.unlink()

            return None

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

        book_filename = book.stored_filename

        if book_filename is not None:
            if book.stored_filename:
                storage_backend.delete_file(
                    user,
                    book.file_hash,
                    book.stored_filename,
                    StorageFileType.BOOK,
                )

            for cover in book.covers:
                storage_backend.delete_file(
                    user,
                    book.file_hash,
                    cover["filename"],
                    StorageFileType.COVER,
                )

        return await book_crud.delete_book_metadata(self.db, book_id)


def get_book_service(
    database: AsyncSession = Depends(get_database),
) -> BookService:
    return BookService(database)
