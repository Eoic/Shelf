import os
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Shelf API"
    PROJECT_VERSION: str = "0.1.0"

    # Server.
    SERVER_HOST: str = os.getenv("SERVER_HOST", "localhost")
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", 8000))
    SERVER_PROTOCOL: str = os.getenv("SERVER_PROTOCOL", "http")

    # Database.
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "shelf")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", 5432))
    TEST_POSTGRES_DB: str = os.getenv("TEST_POSTGRES_DB", "shelf_test")
    TEST_POSTGRES_HOST: str = os.getenv("TEST_POSTGRES_HOST", "localhost")
    TEST_POSTGRES_PORT: int = int(os.getenv("TEST_POSTGRES_PORT", 5433))

    # Files.
    TEMP_FILES_DIR: Path = Path("./storage/temp")
    BOOK_FILES_DIR: Path = Path("./storage/books")
    MINIO_SERVER_HOST: str = os.getenv("MINIO_SERVER_HOST", "localhost")
    MINIO_SERVER_PORT: int = int(os.getenv("MINIO_SERVER_PORT", 9000))
    MINIO_SERVER_PROTOCOL: str = os.getenv("MINIO_SERVER_PROTOCOL", "http")

    # Celery.
    CELERY_BROKER_URL: str | None = None
    CELERY_RESULT_BACKEND: str | None = None

    # Security.
    SECRET_KEY: str | None = os.getenv("SECRET_KEY")

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def test_database_url(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.TEST_POSTGRES_HOST}:{self.TEST_POSTGRES_PORT}/{self.TEST_POSTGRES_DB}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
settings.BOOK_FILES_DIR.mkdir(parents=True, exist_ok=True)
