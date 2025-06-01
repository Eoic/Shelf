import os
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    PROJECT_NAME: str = "E-Book Manager API"
    PROJECT_VERSION: str = "0.1.0"

    # Database
    MONGO_DATABASE_URL: str
    MONGO_DATABASE_NAME: str

    # Storage
    EBOOK_FILES_DIR: Path = Path("./storage/books")
    COVER_FILES_DIR: Path = Path("./storage/covers")
    # Ensure these directories exist or create them at startup
    # Could add a validator or startup hook in main.py

    # Celery (Optional)
    CELERY_BROKER_URL: str | None = None
    CELERY_RESULT_BACKEND: str | None = None

    # Example for JWT, if you add authentication
    # SECRET_KEY: str = "your-secret-key"
    # ALGORITHM: str = "HS256"
    # ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra fields from .env


settings = Settings()

# Create storage directories if they don't exist
# This is a simple way; for more robust solutions, consider startup events in FastAPI
settings.EBOOK_FILES_DIR.mkdir(parents=True, exist_ok=True)
settings.COVER_FILES_DIR.mkdir(parents=True, exist_ok=True)
