from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.schemas.storage_schemas import (
    StorageCreate,
    StorageRead,
    StorageUpdate,
)
from core.auth import get_current_user
from database import get_database
from database.storage_crud import (
    create_storage,
    delete_storage,
    get_all_storages,
    get_storage_by_id,
    update_storage,
)
from models.user import User

router = APIRouter()


@router.post(
    "/",
    response_model=StorageCreate,
    status_code=201,
    summary="Create a new storage method",
)
async def create_storage_record(
    storage_data: StorageCreate,
    db: AsyncSession = Depends(get_database),
    current_user: User = Security(get_current_user),
):
    data = storage_data.model_dump()
    data["user_id"] = current_user.id
    storage = await create_storage(db, data)

    return storage


@router.get(
    "/{storage_id}",
    response_model=StorageCreate,
    summary="Get a storage method by ID",
)
async def get_storage_record(
    storage_id: int,
    db: AsyncSession = Depends(get_database),
    current_user: User = Security(get_current_user),
):
    storage = await get_storage_by_id(db, storage_id)

    if storage is None or getattr(storage, "user_id", None) != current_user.id:
        raise HTTPException(
            status_code=404,
            detail="Storage not found.",
        )

    return storage


@router.get(
    "/",
    response_model=list[StorageRead],
    summary="Get all storage methods for the current user",
)
async def get_all_storage_records(
    db: AsyncSession = Depends(get_database),
    current_user: User = Security(get_current_user),
):
    storages, count = await get_all_storages(db, current_user.id)

    if not storages:
        raise HTTPException(
            status_code=404,
            detail="No storage methods found.",
        )

    return storages


@router.put(
    "/{storage_id}",
    response_model=StorageUpdate,
    summary="Update a storage method by ID",
)
async def update_storage_record(
    storage_id: int,
    storage_update: StorageUpdate,
    db: AsyncSession = Depends(get_database),
    current_user: User = Security(get_current_user),
):
    storage = await get_storage_by_id(db, storage_id)

    if storage is None or getattr(storage, "user_id", None) != current_user.id:
        raise HTTPException(
            status_code=404,
            detail="Storage not found.",
        )

    updated = await update_storage(
        db,
        storage_id,
        storage_update.model_dump(exclude_unset=True),
    )

    return updated


@router.delete(
    "/{storage_id}",
    status_code=204,
    summary="Delete a storage method by ID",
)
async def delete_storage_record(
    storage_id: int,
    db: AsyncSession = Depends(get_database),
    current_user: User = Security(get_current_user),
):
    storage = await get_storage_by_id(db, storage_id)

    if storage is None or getattr(storage, "user_id", None) != current_user.id:
        raise HTTPException(status_code=404, detail="Storage not found.")

    await delete_storage(db, storage_id)
