import shutil
from datetime import datetime
from pathlib import Path
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

from api.v1.schemas.ebook_schemas import (
    EbookDisplay,
    EbookUpdate,
    PaginatedEbookResponse,
)
from services.ebook_service import EbookService, get_ebook_service

router = APIRouter()


# --- Helper function to construct URLs ---
def get_base_url(request: Request) -> str:
    # For production, ensure X-Forwarded-Proto and X-Forwarded-Host are handled if behind a proxy
    return str(request.base_url)


def construct_ebook_display(db_ebook_data: dict, request: Request) -> EbookDisplay:
    base_url = get_base_url(request)
    ebook_data = db_ebook_data.copy()  # Avoid modifying the original dict

    if ebook_data.get("cover_image_filename"):
        ebook_data["cover_image_url"] = (
            f"{base_url}api/v1/ebooks/{ebook_data['_id']}/cover"
        )
    else:
        ebook_data["cover_image_url"] = None

    ebook_data["ebook_download_url"] = (
        f"{base_url}api/v1/ebooks/{ebook_data['_id']}/download"
    )
    return EbookDisplay.model_validate(ebook_data)  # Use model_validate for Pydantic v2


async def process_ebook_upload_task(
    file_path: Path,
    original_filename: str,
    ebook_service: EbookService,  # This would need careful handling with Celery context
):
    # This function would be the target of a Celery task
    # It needs to be self-contained or able to initialize its dependencies
    # For simplicity, we'll call the service method directly in the background task for now
    # If using Celery, ebook_service would not be passed directly.
    # You'd get a new instance within the Celery task.
    print(f"Background task: Processing {original_filename} from {file_path}")

    try:
        # Re-initialize service if this were a true Celery task
        # For FastAPI BackgroundTasks, the dependency injection might carry over,
        # but be mindful of database session scope if using transactional DBs.
        # Motor (MongoDB) is generally fine with this.
        await ebook_service.process_and_save_ebook(file_path, original_filename)
        print(f"Background task: Successfully processed {original_filename}")
    except Exception as e:
        print(f"Background task: Error processing {original_filename}: {e}")
        # TODO: Implement proper error handling/logging and status update for the task
    finally:
        if file_path.exists():  # Clean up the temporary file
            file_path.unlink()


@router.post("/", response_model=EbookDisplay, status_code=201)  # Or 202 if async
async def upload_ebook(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    ebook_service: EbookService = Depends(get_ebook_service),
):
    """
    Uploads an e-book, processes it (metadata, cover), and stores it.
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
        process_ebook_upload_task, temp_file_path, file.filename, ebook_service
    )

    # This response is a placeholder. For true async, you'd return a 202 Accepted
    # with a task ID or a link to check status.
    # For this example, we'll simulate a successful immediate creation for the response model.
    # In a real async setup, you might not have the `created_ebook` immediately.
    # You could return a message like:
    # return {"message": "E-book upload accepted for processing.", "filename": file.filename}

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
        "ebook_download_url": f"{get_base_url(request)}api/v1/ebooks/{placeholder_id}/download",  # Tentative
    }
    # return EbookDisplay.model_validate(placeholder_data) # Pydantic V2
    return {
        "message": "E-book upload accepted for background processing.",
        "filename": file.filename,
        "temp_path": str(temp_file_path),
    }
    # If using Celery:
    # task = process_ebook_upload_task_celery.delay(str(temp_file_path), file.filename)
    # return {"message": "E-book upload accepted for processing.", "task_id": task.id}


@router.get("/", response_model=PaginatedEbookResponse)
async def list_ebooks(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search_query: Optional[str] = Query(None, alias="q"),
    ebook_service: EbookService = Depends(get_ebook_service),
):
    """
    Lists e-books with pagination and optional search.
    """
    ebooks_data, total_items = await ebook_service.get_multiple_ebooks(
        skip=skip, limit=limit, search_query=search_query
    )

    displayed_ebooks = [
        construct_ebook_display(ebook, request) for ebook in ebooks_data
    ]

    total_pages = (total_items + limit - 1) // limit
    return PaginatedEbookResponse(
        total_items=total_items,
        total_pages=total_pages,
        current_page=(skip // limit) + 1,
        items_per_page=limit,
        items=displayed_ebooks,
    )


@router.get("/{ebook_id}", response_model=EbookDisplay)
async def get_ebook_details(
    ebook_id: str,
    request: Request,
    ebook_service: EbookService = Depends(get_ebook_service),
):
    """
    Retrieves metadata for a specific e-book.
    """
    ebook = await ebook_service.get_ebook_by_id(ebook_id)
    if not ebook:
        raise HTTPException(status_code=404, detail="E-book not found")
    return construct_ebook_display(ebook, request)


@router.put("/{ebook_id}", response_model=EbookDisplay)
async def update_ebook_metadata(
    ebook_id: str,
    ebook_update_data: EbookUpdate,
    request: Request,
    ebook_service: EbookService = Depends(get_ebook_service),
):
    """
    Updates metadata for a specific e-book.
    """
    updated_ebook = await ebook_service.update_ebook(ebook_id, ebook_update_data)
    if not updated_ebook:
        raise HTTPException(status_code=404, detail="E-book not found or update failed")
    return construct_ebook_display(updated_ebook, request)


@router.delete("/{ebook_id}", status_code=204)
async def delete_ebook(
    ebook_id: str, ebook_service: EbookService = Depends(get_ebook_service)
):
    """
    Deletes an e-book (metadata and associated files).
    """
    deleted_count = await ebook_service.delete_ebook_by_id(ebook_id)
    if not deleted_count:
        raise HTTPException(
            status_code=404, detail="E-book not found or could not be deleted"
        )
    return None  # FastAPI handles 204 No Content response


@router.get("/{ebook_id}/cover")
async def get_ebook_cover(
    ebook_id: str, ebook_service: EbookService = Depends(get_ebook_service)
):
    """
    Retrieves the cover image for an e-book.
    """
    cover_path, media_type = await ebook_service.get_ebook_cover_path(ebook_id)
    if not cover_path or not cover_path.exists():
        raise HTTPException(status_code=404, detail="Cover image not found")
    # Using FileResponse for efficient streaming
    from fastapi.responses import FileResponse

    return FileResponse(cover_path, media_type=media_type)  # e.g., "image/jpeg"


@router.get("/{ebook_id}/download")
async def download_ebook_file(
    ebook_id: str, ebook_service: EbookService = Depends(get_ebook_service)
):
    """
    Downloads the original e-book file.
    """
    (
        file_path,
        original_filename,
        media_type,
    ) = await ebook_service.get_ebook_file_path_and_details(ebook_id)
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail="E-book file not found")

    from fastapi.responses import FileResponse

    return FileResponse(
        file_path,
        media_type=media_type,  # e.g., "application/epub+zip"
        filename=original_filename,  # This suggests download with original name
    )
