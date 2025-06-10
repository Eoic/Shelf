from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

from api.v1.routes import books as books_v1_router
from api.v1.routes import auth as auth_v1_router
from core.config import settings

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    from pathlib import Path

    Path(settings.BOOK_FILES_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.COVER_FILES_DIR).mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    lifespan=lifespan,
)

app.include_router(
    books_v1_router.router,
    prefix="/api/v1/books",
    tags=["Shelf v1"],
)
app.include_router(
    auth_v1_router.router,
    prefix="/api/v1/auth",
    tags=["Auth v1"],
)


@app.get("/", tags=["Root"])
async def read_root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}!"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
