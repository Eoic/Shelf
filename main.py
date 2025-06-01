from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

from api.v1.routes import books as ebooks_v1_router
from core.config import settings
from database.database import close_mongo_connection, connect_to_mongo

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    from pathlib import Path

    Path(settings.EBOOK_FILES_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.COVER_FILES_DIR).mkdir(parents=True, exist_ok=True)
    yield

    await close_mongo_connection()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    lifespan=lifespan,
)

app.include_router(
    ebooks_v1_router.router,
    prefix="/api/v1/ebooks",
    tags=["Shelf V1"],
)


@app.get("/", tags=["Root"])
async def read_root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}!"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
