from pathlib import Path
import shutil
from typing import Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    UploadFile,
)
from fastapi.responses import FileResponse

from api.v1.schemas.book_schemas import (
    BookDisplay,
    BookUpdate,
    BookUploadQueued,
    PaginatedBookResponse,
)
from core.config import settings
from services.book_service import BookService, get_book_service

router = APIRouter()


def get_base_url(request: Request) -> str:
    return str(request.base_url)


def construct_book_display(db_book_data: dict, request: Request) -> BookDisplay:
    base_url = get_base_url(request)
    book_data = db_book_data.copy()

    if book_data.get("cover_image_filename"):
        book_data["cover_image_url"] = f"{base_url}api/v1/books/{book_data['id']}/cover"
    else:
        book_data["cover_image_url"] = None

    return BookDisplay(**book_data)


@router.post("/", response_model=BookUploadQueued, status_code=201)
async def upload_book(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = Depends(),
    book_service: BookService = Depends(get_book_service),
):
    """
    Uploads a book, processes it (metadata, cover), and stores it.
    Processing is done in the background.
    """
    filename = file.filename or "uploaded_book"
    temp_path = Path("temp") / filename
    temp_path.parent.mkdir(parents=True, exist_ok=True)

    with Path.open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required for book upload",
        )

    background_tasks.add_task(
        book_service.process_and_save_book,
        temp_path,
        file.filename,
    )

    return BookUploadQueued(
        message="Book upload queued",
        filename=file.filename,
        temp_path=str(temp_path),
    )


@router.get("/", response_model=PaginatedBookResponse)
async def list_books(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    book_service: BookService = Depends(get_book_service),
):
    """
    Lists books with pagination and optional search.
    """
    books, total = await book_service.get_multiple_books(skip, limit, search)
    items = [construct_book_display(book.__dict__, request) for book in books]
    return PaginatedBookResponse(items=items, total=total)


@router.get("/{book_id}", response_model=BookDisplay)
async def get_book(
    book_id: int,
    request: Request,
    book_service: BookService = Depends(get_book_service),
):
    """
    Retrieves metadata for a specific book.
    """
    book = await book_service.get_book_by_id(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return construct_book_display(book.__dict__, request)


@router.put("/{book_id}", response_model=BookDisplay)
async def update_book(
    book_id: int,
    book_update: BookUpdate,
    request: Request,
    book_service: BookService = Depends(get_book_service),
):
    """
    Updates metadata for a specific book.
    """
    updated = await book_service.update_book(book_id, book_update)

    if not updated:
        raise HTTPException(status_code=404, detail="Book not found")

    return construct_book_display(updated.__dict__, request)


@router.delete("/{book_id}", status_code=204)
async def delete_book(
    book_id: int,
    book_service: BookService = Depends(get_book_service),
):
    """
    Deletes an book (metadata and associated files).
    """
    deleted = await book_service.delete_book_by_id(book_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Book not found")

    return


@router.get("/{book_id}/cover")
async def get_book_cover(
    book_id: int, book_service: BookService = Depends(get_book_service)
):
    """
    Retrieves the cover image for an book.
    """
    book = await book_service.get_book_by_id(book_id)

    if book.cover_image_filename:
        cover_path = settings.COVER_FILES_DIR / book.cover_image_filename
        return FileResponse(cover_path)

    raise HTTPException(status_code=404, detail="Cover not found")


@router.get("/{book_id}/download")
async def download_book(
    book_id: int, book_service: BookService = Depends(get_book_service)
):
    """
    Downloads the original book file.
    """
    book = await book_service.get_book_by_id(book_id)

    if book.file_path:
        return FileResponse(book.file_path, filename=book.title or "book_file")

    raise HTTPException(status_code=404, detail="File not found")
