from datetime import datetime
from typing import Optional

from pydantic import BaseModel, HttpUrl


class AuthorSchema(BaseModel):
    name: str
    role: Optional[str] = None


class IdentifierSchema(BaseModel):
    type: str
    value: str


class BookBase(BaseModel):
    title: Optional[str] = None
    authors: Optional[list[AuthorSchema]] = None
    publisher: Optional[str] = None
    publication_date: Optional[str] = None
    isbn_10: Optional[str] = None
    isbn_13: Optional[str] = None
    language: Optional[str] = None
    series_name: Optional[str] = None
    series_index: Optional[float] = None
    description: Optional[str] = None
    tags: Optional[list[str]] = []
    identifiers: Optional[list[IdentifierSchema]] = []
    format: Optional[str] = None


class BookCreate(BookBase):
    pass


class BookUpdate(BookBase):
    status: str
    covers: Optional[list[dict[str, str]]] = None
    original_filename: Optional[str] = None
    stored_filename: Optional[str] = None
    file_path: Optional[str] = None
    file_hash: Optional[str] = None
    file_size_bytes: Optional[int] = None


class BookUploadQueued(BaseModel):
    id: str
    title: str
    status: str


class BookDisplay(BookBase):
    id: str
    file_hash: Optional[str] = None
    file_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    download_url: Optional[HttpUrl] = None
    covers: list[dict[str, str]] = []
    original_filename: Optional[str] = None
    stored_filename: Optional[str] = None
    uploaded_at: datetime
    modified_at: Optional[datetime] = None
    status: str
    processing_error: Optional[str] = None

    class Config:
        populate_by_name = True
        from_attributes = True


class BookInDB(BookDisplay):
    user_id: str
    covers: list[dict[str, str]] = []


class PaginatedBookResponse(BaseModel):
    total: int
    items: list[BookDisplay]
