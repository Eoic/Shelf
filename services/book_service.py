import hashlib
import io
import mimetypes
from pathlib import Path
from typing import Any
import uuid

from fastapi import Depends, HTTPException
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.schemas.book_schemas import BookInDB, BookUpdate
from core.config import settings
from core.logger import logger
from database import book_crud
from database.db import get_db
from parsers.base_parser import BookParser
from parsers.epub_parser import EpubParser
from parsers.pdf_parser import PdfParser

PARSER_MAPPING = {
    "EPUB": EpubParser,
    "PDF": PdfParser,
}


class BookService:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db

    async def _get_parser(self, file_path: Path) -> BookParser | None:
        file_format = BookParser.get_file_format(file_path)

        if not file_format:
            logger.error(f"Could not determine file format for {file_path}")
            return None

        parser_class = PARSER_MAPPING.get(file_format)

        if parser_class:
            return parser_class()

        return None

    def _generate_file_hash(self, file_path: Path, hash_algo="md5") -> str:
        hasher = hashlib.new(hash_algo)

        with file_path.open("rb") as file:
            for chunk in iter(lambda: file.read(4096), b""):
                hasher.update(chunk)

        return hasher.hexdigest()

    async def process_and_save_book(  # noqa: C901
        self,
        file_path: Path,
        original_filename: str,
    ) -> BookInDB:
        file_hash = self._generate_file_hash(file_path)
        existing_book = await book_crud.get_book_by_hash(self.db, file_hash)

        if existing_book:
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(
                status_code=409,
                detail=f"Book with same content (hash: {file_hash}) already exists with ID: {existing_book['_id']}",
            )

        parser = await self._get_parser(file_path)

        if not parser:
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(
                status_code=415,
                detail=f"Unsupported file format for {original_filename}",
            )

        extracted_metadata = parser.parse_metadata(file_path)

        if "parsing_error" in extracted_metadata:
            logger.warning(
                f"Metadata parsing issue for {original_filename}: {extracted_metadata['parsing_error']}",
            )

        book_data_to_create: dict[str, Any] = {
            "original_filename": original_filename,
            "md5_hash": file_hash,
            "file_size_bytes": file_path.stat().st_size,
            "format": extracted_metadata.get(
                "format",
                parser.get_file_format(file_path),
            ),
            "title": extracted_metadata.get("title"),
            "authors": extracted_metadata.get("authors", []),
            "publisher": extracted_metadata.get("publisher"),
            "publication_date": extracted_metadata.get("publication_date"),
            "language": extracted_metadata.get("language"),
            "description": extracted_metadata.get("description"),
            "tags": extracted_metadata.get("tags", []),
            "identifiers": extracted_metadata.get("identifiers", []),
        }

        book_data_to_create = {
            k: v for k, v in book_data_to_create.items() if v is not None
        }

        book_internal_id_for_filename = str(uuid.uuid4())
        stored_filename_stem = book_internal_id_for_filename
        stored_file_ext = file_path.suffix

        stored_file_path = (
            settings.BOOK_FILES_DIR / f"{stored_filename_stem}{stored_file_ext}"
        )

        try:
            settings.BOOK_FILES_DIR.mkdir(parents=True, exist_ok=True)
            file_path.rename(stored_file_path)
        except Exception as e:
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(
                status_code=500,
                detail=f"Could not store book file: {e}",
            ) from e

        book_data_to_create["stored_filename"] = (
            f"{stored_filename_stem}{stored_file_ext}"  # Store relative name
        )

        cover_filename = None
        cover_data_tuple = parser.extract_cover_image_data(stored_file_path)

        if cover_data_tuple:
            image_bytes, original_mimetype = cover_data_tuple

            try:
                img = Image.open(io.BytesIO(image_bytes))
                cover_filename_main = f"{stored_filename_stem}_cover.jpg"
                cover_path_main = settings.COVER_FILES_DIR / cover_filename_main
                img.convert("RGB").save(cover_path_main, "JPEG", quality=85)
                cover_filename = cover_filename_main  # Store this in DB

                thumb_filename = f"{stored_filename_stem}_thumb.jpg"
                thumb_path = settings.COVER_FILES_DIR / thumb_filename
                img.thumbnail((150, 200))
                img.convert("RGB").save(thumb_path, "JPEG", quality=80)
            except Exception as e:
                logger.error(
                    f"Could not process/save cover for {original_filename}: {e}",
                )

        if cover_filename:
            book_data_to_create["cover_image_filename"] = cover_filename

        created_db_book = await book_crud.create_book_metadata(
            self.db,
            book_data_to_create,
        )

        return BookInDB.model_validate(created_db_book)

    async def get_multiple_books(
        self,
        skip: int,
        limit: int,
        search_query: str | None,
    ) -> tuple[list[dict[str, Any]], int]:
        books, count = await book_crud.get_all_books(self.db, skip, limit, search_query)

        return [
            BookInDB.model_validate(book.__dict__).model_dump() for book in books
        ], int(
            count or 0,
        )

    async def get_book_by_id(self, book_id: int):
        book = await book_crud.get_book_by_id(self.db, book_id)

        if not book:
            raise HTTPException(status_code=404, detail="Book not found")

        return BookInDB.model_validate(book.__dict__)

    async def update_book(
        self,
        book_id: int,
        book_update_data: BookUpdate,
    ) -> dict[str, Any] | None:
        return await book_crud.update_book_metadata(self.db, book_id, book_update_data)

    async def delete_book_by_id(self, book_id: int) -> int:
        book_to_delete = await book_crud.get_book_by_id(self.db, book_id)

        if not book_to_delete:
            return 0

        if book_to_delete.get("stored_filename"):
            file_to_delete = settings.BOOK_FILES_DIR / book_to_delete["stored_filename"]

            if file_to_delete.exists():
                file_to_delete.unlink()

        if book_to_delete.get("cover_image_filename"):
            cover_to_delete = (
                settings.COVER_FILES_DIR / book_to_delete["cover_image_filename"]
            )

            if cover_to_delete.exists():
                cover_to_delete.unlink()

        return await book_crud.delete_book_metadata(self.db, book_id)

    async def get_book_cover_path(self, book_id: int) -> tuple[Path | None, str | None]:
        book = await self.get_book_by_id(book_id)

        if book and book.cover_image_filename:
            cover_path = settings.COVER_FILES_DIR / book.cover_image_filename

            if cover_path.exists():
                media_type, _ = mimetypes.guess_type(cover_path)
                return cover_path, media_type or "image/jpeg"

        return None, None

    async def get_book_file_path_and_details(
        self,
        book_id: int,
    ) -> tuple[Path | None, str | None, str | None]:
        book = await self.get_book_by_id(book_id)

        if book and book.original_filename and book.format:
            file_path = settings.BOOK_FILES_DIR / book.original_filename

            if file_path.exists():
                media_type, _ = mimetypes.guess_type(file_path)

                if book.format == "EPUB":
                    media_type = media_type or "application/epub+zip"
                elif book.format == "PDF":
                    media_type = media_type or "application/pdf"
                elif book.format.startswith("MOBI"):
                    media_type = media_type or "application/x-mobipocket-book"

                return (
                    file_path,
                    book.original_filename or "book_file",
                    media_type,
                )

        return None, None, None


def get_book_service(
    db: AsyncSession = Depends(get_db),
) -> BookService:
    return BookService(db)
