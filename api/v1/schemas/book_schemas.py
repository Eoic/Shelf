from datetime import datetime

from pydantic import BaseModel, HttpUrl


class AuthorSchema(BaseModel):
    name: str
    role: str | None = None


class IdentifierSchema(BaseModel):
    type: str
    value: str


class BookBase(BaseModel):
    title: str | None = None
    authors: list[AuthorSchema] | None = None
    publisher: str | None = None
    publication_date: str | None = None
    isbn_10: str | None = None
    isbn_13: str | None = None
    language: str | None = None
    series_name: str | None = None
    series_index: float | None = None
    description: str | None = None
    tags: list[str] | None = []
    identifiers: list[IdentifierSchema] | None = []
    format: str | None = None


class BookCreate(BookBase):
    pass


class BookUpdate(BookBase):
    status: str
    covers: list[dict[str, str]] | None = None
    original_filename: str | None = None
    stored_filename: str | None = None
    file_path: str | None = None
    file_hash: str | None = None
    file_size_bytes: int | None = None


class BookUploadQueued(BaseModel):
    id: str
    title: str
    status: str


class BookDisplay(BookBase):
    id: str
    file_hash: str | None = None
    file_path: str | None = None
    file_size_bytes: int | None = None
    download_url: HttpUrl | None = None
    covers: list[dict[str, str]] = []
    original_filename: str | None = None
    stored_filename: str | None = None
    uploaded_at: datetime
    modified_at: datetime | None = None
    status: str
    processing_error: str | None = None

    class Config:
        populate_by_name = True
        from_attributes = True


class BookInDB(BookDisplay):
    user_id: str
    covers: list[dict[str, str]] = []


class PaginatedBookResponse(BaseModel):
    total: int
    items: list[BookDisplay]
