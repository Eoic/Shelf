from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core.crockford import generate_crockford_id
from models.storage import Storage


async def create_storage(
    db: AsyncSession,
    storage_data: dict,
) -> Storage:
    storage_data["id"] = generate_crockford_id()
    storage = Storage(**storage_data)
    db.add(storage)

    await db.commit()
    await db.refresh(storage)

    return storage


async def get_storage_by_id(
    db: AsyncSession,
    storage_id: str,
) -> Storage | None:
    result = await db.execute(select(Storage).where(Storage.id == storage_id))
    return result.scalar_one_or_none()


async def get_all_storages(
    db: AsyncSession,
    user_id: str,
    skip: int = 0,
    limit: int = 10,
):
    query = select(Storage).where(Storage.user_id == user_id).offset(skip).limit(limit)
    result = await db.execute(query)
    storages = result.scalars().all()

    count = await db.scalar(
        select(func.count()).select_from(Storage).where(Storage.user_id == user_id),
    )

    return storages, count


async def get_default_storage(
    db: AsyncSession,
    user_id: str,
) -> Storage | None:
    result = await db.execute(
        select(Storage).where(Storage.is_default & (Storage.user_id == user_id)),
    )

    return result.scalar_one_or_none()


async def update_storage(
    db: AsyncSession,
    storage_id: str,
    storage_data: dict,
) -> Storage | None:
    storage = await get_storage_by_id(db, storage_id)

    if not storage:
        return None

    for key, value in storage_data.items():
        setattr(storage, key, value)

    await db.commit()
    await db.refresh(storage)

    return storage


async def delete_storage(
    db: AsyncSession,
    storage_id: str,
) -> None:
    storage = await get_storage_by_id(db, storage_id)

    if not storage:
        return

    await db.delete(storage)
    await db.commit()
