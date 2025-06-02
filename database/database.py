from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from core.config import settings
from core.logger import logger

# Global client and db variables
client: AsyncIOMotorClient | None = None
db: AsyncIOMotorDatabase | None = None


async def connect_to_mongo():
    global client, db
    logger.info(f"Connecting to MongoDB at {settings.MONGO_DATABASE_URL}...")
    client = AsyncIOMotorClient(settings.MONGO_DATABASE_URL)
    db = client[settings.MONGO_DATABASE_NAME]
    try:
        # The ismaster command is cheap and does not require auth.
        await client.admin.command("ismaster")
        logger.info("Successfully connected to MongoDB!")
    except Exception as e:
        logger.error(f"MongoDB connection failed: {e}")
        # Decide if you want to raise an error and stop the app, or handle reconnects
        raise


async def close_mongo_connection():
    global client
    if client:
        logger.info("Closing MongoDB connection...")
        client.close()
        logger.info("MongoDB connection closed.")


def get_database() -> AsyncIOMotorDatabase:
    if db is None:
        # This should ideally not happen if connect_to_mongo is called at startup
        raise Exception("Database not initialized. Call connect_to_mongo first.")
    return db


# Convenience function for dependency injection
async def get_db_session() -> AsyncIOMotorDatabase:
    return get_database()
