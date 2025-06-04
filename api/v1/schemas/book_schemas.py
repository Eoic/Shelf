from datetime import datetime
from typing import ClassVar, Optional

from bson import ObjectId
from pydantic import BaseModel, Field, HttpUrl
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema


class InvalidObjectIdError(ValueError):
    """Raised when an invalid ObjectId is encountered."""


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, _: core_schema.ValidationInfo):
        if not ObjectId.is_valid(v):
            raise InvalidObjectIdError()

        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(
        cls,
        core_schema: core_schema.CoreSchema,
        handler: JsonSchemaValue,
    ) -> JsonSchemaValue:
        return {"type": "string"}


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
    pass


class BookUploadQueued(BaseModel):
    message: str
    filename: str
    temp_path: str


class BookDisplay(BookBase):
    id: PyObjectId = Field(alias="_id")
    file_size_bytes: Optional[int] = None
    md5_hash: Optional[str] = None
    original_filename: Optional[str] = None
    cover_image_url: Optional[HttpUrl] = None
    book_download_url: Optional[HttpUrl] = None
    upload_timestamp: datetime
    last_modified_timestamp: datetime

    class Config:
        populate_by_name = True
        json_encoders: ClassVar[dict] = {ObjectId: str}
        from_attributes = True


class BookInDB(BookDisplay):
    cover_image_filename: Optional[str] = None


class PaginatedBookResponse(BaseModel):
    total_items: int
    total_pages: int
    current_page: int
    items_per_page: int
    items: list[BookDisplay]
