from pathlib import Path
import shutil
import uuid

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    Security,
    UploadFile,
)
from fastapi.responses import FileResponse

from api.v1.schemas.book_schemas import (
    BookDisplay,
    BookUpdate,
    BookUploadQueued,
    PaginatedBookResponse,
)
from core.auth import get_current_user
from core.config import settings
from models.user import User
from services.book_service import BookService, get_book_service
from services.storage.filesystem_storage import FileSystemStorage
from services.storage.storage_backend import StorageFileType

router = APIRouter()


def get_base_url(request: Request) -> str:
    return str(request.base_url)


def construct_book_display(book_data: dict, request: Request) -> BookDisplay:
    base_url = get_base_url(request)
    book_data = book_data.copy()

    for cover in book_data["covers"]:
        cover["url"] = f"{base_url}api/v1/books/{book_data['id']}/cover?variant={cover['variant']}"

    if "file_path" in book_data:
        book_data["download_url"] = f"{base_url}api/v1/books/{book_data['id']}/download"
    else:
        book_data["download_url"] = None

    return BookDisplay(**book_data)


@router.post(
    "/",
    response_model=BookUploadQueued,
    status_code=201,
    summary="Process and upload a new book",
)
async def upload_book(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    book_service: BookService = Depends(get_book_service),
    user: User = Security(get_current_user),
):
    """
    Uploads a book, processes it (metadata, cover), and stores it.
    Processing is done in the background.
    """
    filename = file.filename or "book.file"
    extension = filename.rsplit(".", 1)[-1].lower()
    temp_file_path = settings.TEMP_FILES_DIR / f"{uuid.uuid4()!s}.{extension}"
    temp_file_path.parent.mkdir(parents=True, exist_ok=True)

    with Path.open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    if not filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required for book upload.",
        )

    user_id = user.id
    book = await book_service.create_queued_book(filename, user_id, temp_file_path)

    if not book:
        raise HTTPException(
            status_code=500,
            detail="Failed to create book metadata.",
        )

    background_tasks.add_task(
        book_service.store_book,
        temp_file_path,
        filename,
        user_id,
        book.id,
    )

    return book


@router.get(
    "/",
    response_model=PaginatedBookResponse,
    summary="List uploaded books",
)
async def list_books(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: str | None = Query(None),
    tags: list[str] | None = Query(None),
    sort_by: str = Query("title", pattern="^(title|uploaded_at)$"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    book_service: BookService = Depends(get_book_service),
    user: User = Security(get_current_user),
):
    """
    Lists books with pagination, optional search, filtering and sorting.
    """
    books, total = await book_service.get_books(
        user.id, skip, limit, search, tags, sort_by, sort_order,
    )
    items = [construct_book_display(book, request) for book in books]
    return PaginatedBookResponse(items=items, total=total)


@router.get(
    "/{book_id}",
    response_model=BookDisplay,
    summary="Get book metadata",
)
async def get_book(
    book_id: str,
    request: Request,
    book_service: BookService = Depends(get_book_service),
    user: User = Security(get_current_user),
):
    """
    Retrieves metadata for a specific book.
    """
    book = await book_service.get_book_by_id(book_id, user.id)

    return construct_book_display(book.__dict__, request)


@router.put(
    "/{book_id}",
    response_model=BookDisplay,
    summary="Update book metadata",
)
async def update_book(
    book_id: str,
    book_update: BookUpdate,
    request: Request,
    book_service: BookService = Depends(get_book_service),
    user: User = Security(get_current_user),
):
    """
    Updates metadata for a specific book.
    """
    updated = await book_service.update_book_by_id(book_id, book_update, user.id)

    if not updated:
        raise HTTPException(status_code=404, detail="Book not found.")

    return construct_book_display(updated.__dict__, request)


@router.delete(
    "/{book_id}",
    status_code=204,
    summary="Delete a book",
)
async def delete_book(
    book_id: str,
    book_service: BookService = Depends(get_book_service),
    user: User = Security(get_current_user),
):
    """
    Deletes an book (metadata and associated files).
    """
    deleted_count = await book_service.delete_book_by_id(user, book_id)

    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="Book not found.")

    return


@router.get(
    "/{book_id}/cover",
    response_class=FileResponse,
    summary="Get book cover (either original or thumbnail)",
)
async def get_book_cover(
    book_id: str,
    background_tasks: BackgroundTasks,
    variant: str | None = Query(
        None,
        description="Cover variant, e.g., 'thumbnail'",
        examples=["thumbnail", "original"],
    ),
    book_service: BookService = Depends(get_book_service),
    user: User = Security(get_current_user),
):
    """
    Retrieves the cover image for a book.
    Optionally, a variant can be requested. Available variants
    depend on the implementation and may include 'thumbnail', 'original', etc.
    """
    book = await book_service.get_book_by_id(book_id, user.id)
    storage_backend = await book_service.get_storage_backend(user)

    if not book.file_hash:
        raise HTTPException(status_code=404, detail="Book does not exist.")

    if variant is None:
        variant = "original"

    for cover in book.covers:
        if cover["variant"] == variant and book.stored_filename:
            cover_path = storage_backend.get_file(
                user,
                book.file_hash,
                cover["filename"],
                StorageFileType.COVER,
            )

            if cover_path and cover_path.exists():
                if not isinstance(storage_backend, FileSystemStorage):
                    background_tasks.add_task(cover_path.unlink)

                return FileResponse(cover_path, background=background_tasks)
            else:
                continue

    raise HTTPException(
        status_code=404,
        detail=f"Cover not found for variant '{variant}'.",
    )


@router.get(
    "/{book_id}/download",
    summary="Download book file",
)
async def download_book_file(
    book_id: str,
    background_tasks: BackgroundTasks,
    book_service: BookService = Depends(get_book_service),
    user: User = Security(get_current_user),
):
    """
    Download the book file for a specific book.
    """
    book = await book_service.get_book_by_id(book_id, user.id)

    if (
        not book.file_path
        or not book.file_hash
        or not book.stored_filename
    ):
        raise HTTPException(status_code=404, detail="File not found.")

    storage_backend = await book_service.get_storage_backend(user)

    book_path = storage_backend.get_file(
        user,
        book.file_hash,
        book.stored_filename,
        StorageFileType.BOOK,
    )

    if not book_path or not book_path.exists():
        raise HTTPException(status_code=404, detail="File not found.")

    if not isinstance(storage_backend, FileSystemStorage):
        background_tasks.add_task(book_path.unlink)

    return FileResponse(
        book_path,
        filename=book.original_filename or book.stored_filename,
        media_type=book.format or "application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{book.original_filename or book.stored_filename}"',
        },
    )


@router.get(
    "/{book_id}/status",
    summary="Get book processing status",
)
async def get_book_status(
    book_id: str,
    book_service: BookService = Depends(get_book_service),
    user: User = Security(get_current_user),
):
    book = await book_service.get_book_by_id(book_id, user.id)

    return {"status": book.status, "error": book.processing_error}
