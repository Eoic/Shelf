from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path

from models.user import User


class StorageFileType(Enum):
    BOOK = "book"
    COVER = "cover"


class StorageBackend(ABC):
    @abstractmethod
    def get_file(
        self,
        user: User,
        book_dir: str,
        filename: str,
        filetype: StorageFileType,
    ) -> Path | None:
        """Retrieve a file by its storage identifier (book directory and optional subfilename)."""
        pass

    @abstractmethod
    def store_file(
        self,
        user: User,
        source: Path,
        book_dir: str,
        filename: str,
        filetype: StorageFileType,
    ) -> Path:
        """Store a file and return the storage path or identifier."""
        pass

    @abstractmethod
    def delete_file(
        self,
        user: User,
        book_dir: str,
        filename: str,
        filetype: StorageFileType,
    ) -> bool:
        """Delete a file by its storage identifier and type."""
        pass

    @abstractmethod
    def get_prepared_book_dir(self, user: User, book_dir: str) -> Path:
        """
        Return the book directory for the given user and book_dir, and ensure it exists.
        """
        pass
