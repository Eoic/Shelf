from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime
import re  # For regex search

from api.v1.schemas.ebook_schemas import (
    EbookCreate,
    EbookUpdate,
    EbookInDB,
)  # Using EbookCreate for structure

EBOOK_COLLECTION = "ebooks"


# --- Helper to convert Pydantic model to dict for MongoDB, handling None values ---
def model_to_dict(model, exclude_unset=True, exclude_none=True):
    return model.model_dump(
        exclude_unset=exclude_unset, exclude_none=exclude_none
    )  # Pydantic V2


async def create_ebook_metadata(
    db: AsyncIOMotorDatabase, ebook_data: Dict[str, Any]
) -> Dict[str, Any]:
    ebook_data["upload_timestamp"] = datetime.utcnow()
    ebook_data["last_modified_timestamp"] = datetime.utcnow()
    result = await db[EBOOK_COLLECTION].insert_one(ebook_data)
    created_ebook = await db[EBOOK_COLLECTION].find_one({"_id": result.inserted_id})
    return created_ebook  # type: ignore


async def get_ebook_by_id(
    db: AsyncIOMotorDatabase, ebook_id: str
) -> Optional[Dict[str, Any]]:
    if not ObjectId.is_valid(ebook_id):
        return None
    return await db[EBOOK_COLLECTION].find_one({"_id": ObjectId(ebook_id)})


async def get_ebook_by_hash(
    db: AsyncIOMotorDatabase, file_hash: str
) -> Optional[Dict[str, Any]]:
    return await db[EBOOK_COLLECTION].find_one(
        {"md5_hash": file_hash}
    )  # Or whatever hash you use


async def get_all_ebooks(
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

    cursor = db[EBOOK_COLLECTION].find(query_filter).skip(skip).limit(limit)
    ebooks = await cursor.to_list(length=limit)
    total_count = await db[EBOOK_COLLECTION].count_documents(query_filter)
    return ebooks, total_count


async def update_ebook_metadata(
    db: AsyncIOMotorDatabase, ebook_id: str, ebook_update_data: EbookUpdate
) -> Optional[Dict[str, Any]]:
    if not ObjectId.is_valid(ebook_id):
        return None

    update_data = model_to_dict(
        ebook_update_data, exclude_unset=True, exclude_none=True
    )
    if not update_data:  # No actual fields to update
        return await get_ebook_by_id(db, ebook_id)  # Return current data

    update_data["last_modified_timestamp"] = datetime.utcnow()

    result = await db[EBOOK_COLLECTION].find_one_and_update(
        {"_id": ObjectId(ebook_id)},
        {"$set": update_data},
        return_document=True,  # MongoDB specific: use ReturnDocument.AFTER with PyMongo
    )
    return result


async def delete_ebook_metadata(db: AsyncIOMotorDatabase, ebook_id: str) -> int:
    if not ObjectId.is_valid(ebook_id):
        return 0
    result = await db[EBOOK_COLLECTION].delete_one({"_id": ObjectId(ebook_id)})
    return result.deleted_count
