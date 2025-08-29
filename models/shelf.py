from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import Column, DateTime, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from database.base import Base

if TYPE_CHECKING:
    from models.book import Book

shelf_books = Table(
    "shelf_books",
    Base.metadata,
    Column("shelf_id", String, ForeignKey("shelves.id", ondelete="CASCADE"), primary_key=True),
    Column("book_id", String, ForeignKey("books.id", ondelete="CASCADE"), primary_key=True),
)


class Shelf(Base):
    __tablename__ = "shelves"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[Any] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[Any] = mapped_column(DateTime, onupdate=func.now(), nullable=True)
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
    )

    books: Mapped[list[Book]] = relationship(
        "Book", secondary="shelf_books", back_populates="shelves",
    )
