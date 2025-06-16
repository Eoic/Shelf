from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from api.v1.schemas.book_schemas import BookUpdate
from models.domain_models import Book


async def create_book_metadata(
    db: AsyncSession,
    book_data: dict,
) -> Book:
    book = Book(**book_data)
    db.add(book)

    await db.commit()
    await db.refresh(book)

    return book


async def get_book_by_id(
    db: AsyncSession,
    book_id: str,
) -> Book | None:
    result = await db.execute(select(Book).where(Book.id == book_id))
    return result.scalar_one_or_none()


async def get_book_by_hash(
    db: AsyncSession,
    file_hash: str,
) -> Book | None:
    result = await db.execute(select(Book).where(Book.file_hash == file_hash))
    return result.scalar_one_or_none()


async def get_all_books(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 10,
    search_query: str | None = None,
):
    query = select(Book)

    if search_query:
        query = query.where(Book.title.ilike(f"%{search_query}%"))

    result = await db.execute(query.offset(skip).limit(limit))
    books = result.scalars().all()
    count = await db.scalar(select(func.count()).select_from(Book))

    return books, count


async def update_book_metadata(
    db: AsyncSession,
    book_id: str,
    book_update_data: BookUpdate,
) -> Book | None:
    book = await get_book_by_id(db, book_id)

    if not book:
        return None

    for field, value in book_update_data.model_dump(exclude_unset=True).items():
        setattr(book, field, value)

    await db.commit()
    await db.refresh(book)
    return book


async def delete_book_metadata(db: AsyncSession, book_id: str) -> int:
    book = await get_book_by_id(db, book_id)

    if not book:
        return 0

    await db.delete(book)
    await db.commit()

    return 1
