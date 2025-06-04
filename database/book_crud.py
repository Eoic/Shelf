from datetime import datetime, timezone
import re
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from api.v1.schemas.book_schemas import BookUpdate

BOOK_COLLECTION = "books"


def model_to_dict(model, exclude_unset=True, exclude_none=True):
    return model.model_dump(exclude_unset=exclude_unset, exclude_none=exclude_none)


async def create_book_metadata(
    db: AsyncIOMotorDatabase,
    book_data: dict[str, Any],
) -> dict[str, Any]:
    book_data["upload_timestamp"] = datetime.now(timezone.utc)
    book_data["last_modified_timestamp"] = datetime.now(timezone.utc)
    result = await db[BOOK_COLLECTION].insert_one(book_data)
    created_book = await db[BOOK_COLLECTION].find_one({"_id": result.inserted_id})

    return created_book  # type: ignore


async def get_book_by_id(
    db: AsyncIOMotorDatabase,
    book_id: str,
) -> dict[str, Any] | None:
    if not ObjectId.is_valid(book_id):
        return None

    return await db[BOOK_COLLECTION].find_one({"_id": ObjectId(book_id)})


async def get_book_by_hash(
    db: AsyncIOMotorDatabase,
    file_hash: str,
) -> dict[str, Any] | None:
    return await db[BOOK_COLLECTION].find_one({"md5_hash": file_hash})


async def get_all_books(
    db: AsyncIOMotorDatabase,
    skip: int = 0,
    limit: int = 10,
    search_query: str | None = None,
) -> tuple[list[dict[str, Any]], int]:
    query_filter = {}

    if search_query:
        regex = re.compile(f".*{re.escape(search_query)}.*", re.IGNORECASE)

        query_filter["$or"] = [
            {"title": {"$regex": regex}},
            {"authors.name": {"$regex": regex}},
            {"tags": {"$regex": regex}},
        ]

    cursor = db[BOOK_COLLECTION].find(query_filter).skip(skip).limit(limit)
    books = await cursor.to_list(length=limit)
    total_count = await db[BOOK_COLLECTION].count_documents(query_filter)

    return books, total_count


async def update_book_metadata(
    db: AsyncIOMotorDatabase,
    book_id: str,
    book_update_data: BookUpdate,
) -> dict[str, Any] | None:
    if not ObjectId.is_valid(book_id):
        return None

    update_data = model_to_dict(book_update_data, exclude_unset=True, exclude_none=True)

    if not update_data:
        return await get_book_by_id(db, book_id)

    update_data["last_modified_timestamp"] = datetime.now(timezone.utc)

    result = await db[BOOK_COLLECTION].find_one_and_update(
        {"_id": ObjectId(book_id)},
        {"$set": update_data},
        return_document=True,
    )

    return result


async def delete_book_metadata(db: AsyncIOMotorDatabase, book_id: str) -> int:
    if not ObjectId.is_valid(book_id):
        return 0

    result = await db[BOOK_COLLECTION].delete_one({"_id": ObjectId(book_id)})
    return result.deleted_count
