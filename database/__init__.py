from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from core.config import settings

DATABASE_URL = settings.database_url

engine = create_async_engine(DATABASE_URL, echo=True, future=True)

async_session = async_sessionmaker(
    engine,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_database():
    async with async_session() as session:
        yield session
