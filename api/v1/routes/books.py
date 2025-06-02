from datetime import datetime, timezone
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
    PaginatedBookResponse,
)
from core.logger import logger
from services.book_service import BookService, get_book_service

router = APIRouter()


def get_base_url(request: Request) -> str:
    return str(request.base_url)


def construct_book_display(db_book_data: dict, request: Request) -> BookDisplay:
    base_url = get_base_url(request)
    book_data = db_book_data.copy()

    if book_data.get("cover_image_filename"):
        book_data["cover_image_url"] = (
            f"{base_url}api/v1/books/{book_data['_id']}/cover"
        )
    else:
        book_data["cover_image_url"] = None

    book_data["book_download_url"] = (
        f"{base_url}api/v1/books/{book_data['_id']}/download"
    )

    return BookDisplay.model_validate(book_data)


async def process_book_upload_task(
    file_path: Path,
    original_filename: str,
    book_service: BookService,
):
    logger.info(f"Background task: Processing {original_filename} from {file_path}")

    try:
        await book_service.process_and_save_book(file_path, original_filename)
        logger.info(f"Background task: Successfully processed {original_filename}")
    except Exception as e:
        logger.error(f"Background task: Error processing {original_filename}: {e}")
    finally:
        if file_path.exists():
            file_path.unlink()


@router.post("/", response_model=BookDisplay, status_code=201)
async def upload_book(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    book_service: BookService = Depends(get_book_service),
):
    """
    Uploads an book, processes it (metadata, cover), and stores it.
    Processing is done in the background.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    temp_dir = Path("temp_uploads")
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_file_path = temp_dir / f"{file.filename}"

    try:
        with temp_file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Could not save uploaded file: {e}",
        ) from e
    finally:
        file.file.close()

    background_tasks.add_task(
        process_book_upload_task,
        temp_file_path,
        file.filename,
        book_service,
    )

    # placeholder_id = "605c72ef98dab1a8d2f00000"

    # placeholder_data = {
    #     "_id": placeholder_id,
    #     "title": f"Processing: {file.filename}",
    #     "original_filename": file.filename,
    #     "upload_timestamp": datetime.now(timezone.utc),
    #     "last_modified_timestamp": datetime.now(timezone.utc),
    #     "cover_image_url": None,
    #     "book_download_url": f"{get_base_url(request)}api/v1/books/{placeholder_id}/download",  # Tentative
    # }

    # return BookDisplay.model_validate(placeholder_data)

    return {
        "message": "Book upload accepted for background processing.",
        "filename": file.filename,
        "temp_path": str(temp_file_path),
    }

    # Celery:
    # task = process_book_upload_task_celery.delay(str(temp_file_path), file.filename)
    # return {"message": "Book upload accepted for processing.", "task_id": task.id}


@router.get("/", response_model=PaginatedBookResponse)
async def list_books(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search_query: Optional[str] = Query(None, alias="q"),
    book_service: BookService = Depends(get_book_service),
):
    """
    Lists books with pagination and optional search.
    """
    books_data, total_items = await book_service.get_multiple_books(
        skip=skip,
        limit=limit,
        search_query=search_query,
    )

    displayed_books = [construct_book_display(book, request) for book in books_data]
    total_pages = (total_items + limit - 1) // limit

    return PaginatedBookResponse(
        total_items=total_items,
        total_pages=total_pages,
        current_page=(skip // limit) + 1,
        items_per_page=limit,
        items=displayed_books,
    )


@router.get("/{book_id}", response_model=BookDisplay)
async def get_book_details(
    book_id: str,
    request: Request,
    book_service: BookService = Depends(get_book_service),
):
    """
    Retrieves metadata for a specific book.
    """
    book = await book_service.get_book_by_id(book_id)

    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    return construct_book_display(book, request)


@router.put("/{book_id}", response_model=BookDisplay)
async def update_book_metadata(
    book_id: str,
    book_update_data: BookUpdate,
    request: Request,
    book_service: BookService = Depends(get_book_service),
):
    """
    Updates metadata for a specific book.
    """
    updated_book = await book_service.update_book(book_id, book_update_data)

    if not updated_book:
        raise HTTPException(status_code=404, detail="Book not found or update failed")

    return construct_book_display(updated_book, request)


@router.delete("/{book_id}", status_code=204)
async def delete_book(
    book_id: str,
    book_service: BookService = Depends(get_book_service),
):
    """
    Deletes an book (metadata and associated files).
    """
    deleted_count = await book_service.delete_book_by_id(book_id)

    if not deleted_count:
        raise HTTPException(
            status_code=404,
            detail="Book not found or could not be deleted",
        )

    return None


@router.get("/{book_id}/cover")
async def get_book_cover(
    book_id: str, book_service: BookService = Depends(get_book_service)
):
    """
    Retrieves the cover image for an book.
    """
    cover_path, media_type = await book_service.get_book_cover_path(book_id)

    if not cover_path or not cover_path.exists():
        raise HTTPException(status_code=404, detail="Cover image not found")

    return FileResponse(cover_path, media_type=media_type)


@router.get("/{book_id}/download")
async def download_book_file(
    book_id: str, book_service: BookService = Depends(get_book_service)
):
    """
    Downloads the original book file.
    """
    (
        file_path,
        original_filename,
        media_type,
    ) = await book_service.get_book_file_path_and_details(book_id)
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail="Book file not found")

    return FileResponse(
        file_path,
        media_type=media_type,
        filename=original_filename,
    )
