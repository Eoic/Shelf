from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime
import re  # For regex search

from api.v1.schemas.book_schemas import (
    BookCreate,
    BookUpdate,
    BookInDB,
)  # Using BookCreate for structure

BOOK_COLLECTION = "books"


# --- Helper to convert Pydantic model to dict for MongoDB, handling None values ---
def model_to_dict(model, exclude_unset=True, exclude_none=True):
    return model.model_dump(
        exclude_unset=exclude_unset, exclude_none=exclude_none
    )  # Pydantic V2


async def create_book_metadata(
    db: AsyncIOMotorDatabase, book_data: Dict[str, Any]
) -> Dict[str, Any]:
    book_data["upload_timestamp"] = datetime.utcnow()
    book_data["last_modified_timestamp"] = datetime.utcnow()
    result = await db[BOOK_COLLECTION].insert_one(book_data)
    created_book = await db[BOOK_COLLECTION].find_one({"_id": result.inserted_id})
    return created_book  # type: ignore


async def get_book_by_id(
    db: AsyncIOMotorDatabase, book_id: str
) -> Optional[Dict[str, Any]]:
    if not ObjectId.is_valid(book_id):
        return None
    return await db[BOOK_COLLECTION].find_one({"_id": ObjectId(book_id)})


async def get_book_by_hash(
    db: AsyncIOMotorDatabase, file_hash: str
) -> Optional[Dict[str, Any]]:
    return await db[BOOK_COLLECTION].find_one(
        {"md5_hash": file_hash}
    )  # Or whatever hash you use


async def get_all_books(
    db: AsyncIOMotorDatabase,
    skip: int = 0,
    limit: int = 10,
    search_query: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], int]:
    query_filter = {}
    if search_query:
        # Simple case-insensitive search on title and authors
        # For more advanced search, consider MongoDB text indexes or Elasticsearch
        regex = re.compile(f".*{re.escape(search_query)}.*", re.IGNORECASE)
        query_filter["$or"] = [
            {"title": {"$regex": regex}},
            {"authors.name": {"$regex": regex}},  # Assuming authors is a list of dicts
            {"tags": {"$regex": regex}},  # Assuming tags is a list of strings
        ]

    cursor = db[BOOK_COLLECTION].find(query_filter).skip(skip).limit(limit)
    books = await cursor.to_list(length=limit)
    total_count = await db[BOOK_COLLECTION].count_documents(query_filter)
    return books, total_count


async def update_book_metadata(
    db: AsyncIOMotorDatabase, book_id: str, book_update_data: BookUpdate
) -> Optional[Dict[str, Any]]:
    if not ObjectId.is_valid(book_id):
        return None

    update_data = model_to_dict(book_update_data, exclude_unset=True, exclude_none=True)
    if not update_data:  # No actual fields to update
        return await get_book_by_id(db, book_id)  # Return current data

    update_data["last_modified_timestamp"] = datetime.utcnow()

    result = await db[BOOK_COLLECTION].find_one_and_update(
        {"_id": ObjectId(book_id)},
        {"$set": update_data},
        return_document=True,  # MongoDB specific: use ReturnDocument.AFTER with PyMongo
    )
    return result


async def delete_book_metadata(db: AsyncIOMotorDatabase, book_id: str) -> int:
    if not ObjectId.is_valid(book_id):
        return 0
    result = await db[BOOK_COLLECTION].delete_one({"_id": ObjectId(book_id)})
    return result.deleted_count
