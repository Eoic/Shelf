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
        filename: str,
        filetype: StorageFileType,
    ) -> Path | None:
        """Retrieve a file by its storage identifier."""
        pass

    @abstractmethod
    def store_file(
        self,
        user: User,
        source: Path,
        filename: str,
        filetype: StorageFileType,
    ) -> Path:
        """Store a file and return the storage path or identifier."""
        pass

    @abstractmethod
    def delete_file(
        self,
        user: User,
        filename: str,
        filetype: StorageFileType,
    ) -> bool:
        """Delete a file by its storage identifier and type."""
        pass
