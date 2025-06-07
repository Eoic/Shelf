from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.sql import func

from database.base import Base


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=True)
    authors = Column(MutableList.as_mutable(ARRAY(JSON)), nullable=True)
    publisher = Column(String, nullable=True)
    publication_date = Column(String, nullable=True)
    isbn_10 = Column(String, nullable=True)
    isbn_13 = Column(String, nullable=True)
    language = Column(String, nullable=True)
    series_name = Column(String, nullable=True)
    series_index = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    tags = Column(MutableList.as_mutable(ARRAY(String)), default=[])
    identifiers = Column(MutableList.as_mutable(ARRAY(JSON)), default=[])
    format = Column(String, nullable=True)
    cover_image_filename = Column(String, nullable=True)
    file_hash = Column(String, nullable=True, unique=True)
    file_path = Column(String, nullable=True)
    upload_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    last_modified_timestamp = Column(DateTime(timezone=True), onupdate=func.now())
