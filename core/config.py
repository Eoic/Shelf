from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Shelf API"
    PROJECT_VERSION: str = "0.1.0"

    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str = "shelf"

    BOOK_FILES_DIR: Path = Path("./storage/books")
    COVER_FILES_DIR: Path = Path("./storage/covers")

    CELERY_BROKER_URL: str | None = None
    CELERY_RESULT_BACKEND: str | None = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
settings.BOOK_FILES_DIR.mkdir(parents=True, exist_ok=True)
settings.COVER_FILES_DIR.mkdir(parents=True, exist_ok=True)
