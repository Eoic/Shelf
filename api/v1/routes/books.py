from datetime import datetime
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

from api.v1.schemas.book_schemas import (
    BookDisplay,
    BookUpdate,
    PaginatedBookResponse,
)
from services.book_service import Bookservice, get_book_service

router = APIRouter()


def get_base_url(request: Request) -> str:
    # For production, ensure X-Forwarded-Proto and X-Forwarded-Host are handled if behind a proxy
    return str(request.base_url)


def construct_book_display(db_book_data: dict, request: Request) -> BookDisplay:
    base_url = get_base_url(request)
    book_data = db_book_data.copy()  # Avoid modifying the original dict

    if book_data.get("cover_image_filename"):
        book_data["cover_image_url"] = (
            f"{base_url}api/v1/books/{book_data['_id']}/cover"
        )
    else:
        book_data["cover_image_url"] = None

    book_data["book_download_url"] = (
        f"{base_url}api/v1/books/{book_data['_id']}/download"
    )
    return BookDisplay.model_validate(book_data)  # Use model_validate for Pydantic v2


async def process_book_upload_task(
    file_path: Path,
    original_filename: str,
    book_service: Bookservice,  # This would need careful handling with Celery context
):
    # This function would be the target of a Celery task
    # It needs to be self-contained or able to initialize its dependencies
    # For simplicity, we'll call the service method directly in the background task for now
    # If using Celery, book_service would not be passed directly.
    # You'd get a new instance within the Celery task.
    print(f"Background task: Processing {original_filename} from {file_path}")

    try:
        # Re-initialize service if this were a true Celery task
        # For FastAPI BackgroundTasks, the dependency injection might carry over,
        # but be mindful of database session scope if using transactional DBs.
        # Motor (MongoDB) is generally fine with this.
        await book_service.process_and_save_book(file_path, original_filename)
        print(f"Background task: Successfully processed {original_filename}")
    except Exception as e:
        print(f"Background task: Error processing {original_filename}: {e}")
        # TODO: Implement proper error handling/logging and status update for the task
    finally:
        if file_path.exists():  # Clean up the temporary file
            file_path.unlink()


@router.post("/", response_model=BookDisplay, status_code=201)  # Or 202 if async
async def upload_book(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    book_service: Bookservice = Depends(get_book_service),
):
    """
    Uploads an book, processes it (metadata, cover), and stores it.
    Processing is done in the background.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    # Create a temporary path to save the uploaded file
    # Ensure this temp location is secure and cleaned up
    temp_dir = Path("temp_uploads")
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_file_path = (
        temp_dir / f"{file.filename}"
    )  # Consider using uuid for temp filenames

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

    # For now, trigger background task and return a "processing" response placeholder
    # A more robust solution would involve a task ID and status polling.
    background_tasks.add_task(
        process_book_upload_task, temp_file_path, file.filename, book_service
    )

    # This response is a placeholder. For true async, you'd return a 202 Accepted
    # with a task ID or a link to check status.
    # For this example, we'll simulate a successful immediate creation for the response model.
    # In a real async setup, you might not have the `created_book` immediately.
    # You could return a message like:
    # return {"message": "Book upload accepted for processing.", "filename": file.filename}

    # SIMULATED immediate response for the sake of the response_model.
    # In a real async scenario, this data wouldn't be available yet.
    # You might need a different response model for the 202 case.
    # For now, let's pretend we have some initial data (this is NOT how it would actually work async)
    placeholder_id = "605c72ef98dab1a8d2f00000"  # Example ObjectId string
    placeholder_data = {
        "_id": placeholder_id,
        "title": f"Processing: {file.filename}",
        "original_filename": file.filename,
        "upload_timestamp": datetime.utcnow(),
        "last_modified_timestamp": datetime.utcnow(),
        "cover_image_url": None,  # Will be populated after processing
        "book_download_url": f"{get_base_url(request)}api/v1/books/{placeholder_id}/download",  # Tentative
    }
    # return BookDisplay.model_validate(placeholder_data) # Pydantic V2
    return {
        "message": "Book upload accepted for background processing.",
        "filename": file.filename,
        "temp_path": str(temp_file_path),
    }
    # If using Celery:
    # task = process_book_upload_task_celery.delay(str(temp_file_path), file.filename)
    # return {"message": "Book upload accepted for processing.", "task_id": task.id}


@router.get("/", response_model=PaginatedBookResponse)
async def list_books(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search_query: Optional[str] = Query(None, alias="q"),
    book_service: Bookservice = Depends(get_book_service),
):
    """
    Lists books with pagination and optional search.
    """
    books_data, total_items = await book_service.get_multiple_books(
        skip=skip, limit=limit, search_query=search_query
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
    book_service: Bookservice = Depends(get_book_service),
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
    book_service: Bookservice = Depends(get_book_service),
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
    book_id: str, book_service: Bookservice = Depends(get_book_service)
):
    """
    Deletes an book (metadata and associated files).
    """
    deleted_count = await book_service.delete_book_by_id(book_id)
    if not deleted_count:
        raise HTTPException(
            status_code=404, detail="Book not found or could not be deleted"
        )
    return None  # FastAPI handles 204 No Content response


@router.get("/{book_id}/cover")
async def get_book_cover(
    book_id: str, book_service: Bookservice = Depends(get_book_service)
):
    """
    Retrieves the cover image for an book.
    """
    cover_path, media_type = await book_service.get_book_cover_path(book_id)
    if not cover_path or not cover_path.exists():
        raise HTTPException(status_code=404, detail="Cover image not found")
    # Using FileResponse for efficient streaming
    from fastapi.responses import FileResponse

    return FileResponse(cover_path, media_type=media_type)  # e.g., "image/jpeg"


@router.get("/{book_id}/download")
async def download_book_file(
    book_id: str, book_service: Bookservice = Depends(get_book_service)
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

    from fastapi.responses import FileResponse

    return FileResponse(
        file_path,
        media_type=media_type,  # e.g., "application/epub+zip"
        filename=original_filename,  # This suggests download with original name
    )
