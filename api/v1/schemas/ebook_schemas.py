import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

# For ObjectId handling with Pydantic if using MongoDB
from bson import ObjectId
from pydantic import BaseModel, Field, HttpUrl
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, _: core_schema.ValidationInfo):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: core_schema.CoreSchema, handler: JsonSchemaValue
    ) -> JsonSchemaValue:
        return {"type": "string"}


class AuthorSchema(BaseModel):
    name: str
    role: Optional[str] = None


class IdentifierSchema(BaseModel):
    type: str  # e.g., ISBN, DOI, UUID
    value: str


# Base model for common fields
class EbookBase(BaseModel):
    title: Optional[str] = None
    authors: Optional[List[AuthorSchema]] = None
    publisher: Optional[str] = None
    publication_date: Optional[str] = None  # Or datetime if you enforce strict parsing
    isbn_10: Optional[str] = None
    isbn_13: Optional[str] = None
    language: Optional[str] = None
    series_name: Optional[str] = None
    series_index: Optional[float] = None  # Or str
    description: Optional[str] = None
    tags: Optional[List[str]] = []
    identifiers: Optional[List[IdentifierSchema]] = []
    # page_count: Optional[int] = None # Often hard to get accurately
    format: Optional[str] = None


# Schema for creating an e-book (metadata might be extracted from file)
class EbookCreate(EbookBase):
    # Typically, most fields will be extracted during parsing,
    # but you might allow some overrides via API on upload.
    pass


# Schema for updating an e-book
class EbookUpdate(EbookBase):
    # All fields are optional for PATCH-like updates
    pass


# Schema for displaying e-book metadata
class EbookDisplay(EbookBase):
    id: PyObjectId = Field(alias="_id")  # For MongoDB's default _id
    # internal_id: uuid.UUID # If you use a separate UUID
    file_size_bytes: Optional[int] = None
    md5_hash: Optional[str] = None
    original_filename: Optional[str] = None
    cover_image_url: Optional[HttpUrl] = None  # Constructed URL
    ebook_download_url: Optional[HttpUrl] = None  # Constructed URL
    upload_timestamp: datetime
    last_modified_timestamp: datetime

    class Config:
        populate_by_name = True  # Allows using '_id' from MongoDB
        json_encoders = {ObjectId: str}  # Serialize ObjectId to str
        # orm_mode is deprecated, use from_attributes=True in Pydantic v2
        from_attributes = True


class EbookInDB(EbookDisplay):  # For data directly from DB before constructing URLs
    cover_image_filename: Optional[str] = None
    # No URLs here, just the raw data
    pass


class PaginatedEbookResponse(BaseModel):
    total_items: int
    total_pages: int
    current_page: int
    items_per_page: int
    items: List[EbookDisplay]
