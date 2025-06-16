from typing import Any

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSON
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from database.base import Base


class Book(Base):
    __tablename__ = "books"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    title: Mapped[str | None] = mapped_column(String, nullable=True)

    authors: Mapped[list[Any] | None] = mapped_column(
        MutableList.as_mutable(ARRAY(JSON)),
        nullable=True,
    )

    publisher: Mapped[str | None] = mapped_column(String, nullable=True)
    publication_date: Mapped[str | None] = mapped_column(String, nullable=True)
    isbn_10: Mapped[str | None] = mapped_column(String, nullable=True)
    isbn_13: Mapped[str | None] = mapped_column(String, nullable=True)
    language: Mapped[str | None] = mapped_column(String, nullable=True)
    series_name: Mapped[str | None] = mapped_column(String, nullable=True)
    series_index: Mapped[float | None] = mapped_column(Float, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    tags: Mapped[list[str]] = mapped_column(
        MutableList.as_mutable(ARRAY(String)),
        nullable=True,
        default=list,
    )

    identifiers: Mapped[list[Any]] = mapped_column(
        MutableList.as_mutable(ARRAY(JSON)),
        nullable=True,
        default=list,
    )

    covers = mapped_column(
        MutableList.as_mutable(ARRAY(JSON)),
        nullable=False,
        default=list,
    )

    format: Mapped[str | None] = mapped_column(String, nullable=True)
    original_filename: Mapped[str | None] = mapped_column(String, nullable=True)
    stored_filename: Mapped[str | None] = mapped_column(String, nullable=True)
    file_hash: Mapped[str | None] = mapped_column(String, nullable=True, unique=True)
    file_path: Mapped[str | None] = mapped_column(String, nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    uploaded_at: Mapped[Any] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=True,
    )

    modified_at: Mapped[Any] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True,
    )
