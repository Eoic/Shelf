from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models.storage import Storage


async def create_storage(
    db: AsyncSession,
    storage_data: dict,
) -> Storage:
    storage = Storage(**storage_data)
    db.add(storage)

    await db.commit()
    await db.refresh(storage)

    return storage


async def get_storage_by_id(
    db: AsyncSession,
    storage_id: int,
) -> Storage | None:
    result = await db.execute(select(Storage).where(Storage.id == storage_id))
    return result.scalar_one_or_none()


async def update_storage(
    db: AsyncSession,
    storage_id: int,
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
    storage_id: int,
) -> None:
    storage = await get_storage_by_id(db, storage_id)

    if not storage:
        return

    await db.delete(storage)
    await db.commit()
