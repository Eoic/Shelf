from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from core.crockford import generate_crockford_id
from models.book import Book
from models.shelf import Shelf


async def create_shelf(db: AsyncSession, user_id: str, name: str) -> Shelf:
    shelf = Shelf(id=generate_crockford_id(), user_id=user_id, name=name)
    db.add(shelf)
    await db.commit()
    await db.refresh(shelf)
    return shelf


async def get_shelves(db: AsyncSession, user_id: str) -> list[Shelf]:
    result = await db.execute(
        select(Shelf).where(Shelf.user_id == user_id).options(selectinload(Shelf.books)),
    )
    return result.scalars().all()


async def get_shelf(
    db: AsyncSession,
    shelf_id: str,
    user_id: str,
) -> Shelf | None:
    result = await db.execute(
        select(Shelf).where(Shelf.id == shelf_id, Shelf.user_id == user_id).options(selectinload(Shelf.books)),
    )
    return result.scalars().first()


async def delete_shelf(db: AsyncSession, shelf: Shelf) -> None:
    await db.delete(shelf)
    await db.commit()


async def add_book(db: AsyncSession, shelf: Shelf, book: Book) -> Shelf:
    if book not in shelf.books:
        shelf.books.append(book)
        await db.commit()
        await db.refresh(shelf)
    return shelf


async def remove_book(db: AsyncSession, shelf: Shelf, book: Book) -> Shelf:
    if book in shelf.books:
        shelf.books.remove(book)
        await db.commit()
        await db.refresh(shelf)
    return shelf
