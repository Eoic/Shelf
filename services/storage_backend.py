from abc import ABC, abstractmethod
from pathlib import Path


class StorageBackend(ABC):
    @abstractmethod
    def get_file(self, file_id: str) -> Path | None:
        """Retrieve a file by its storage identifier. Returns a Path or None."""
        pass

    @abstractmethod
    def store_file(self, src_path: Path, dst_name: str) -> str:
        """Store a file and return the storage path or identifier."""
        pass

    @abstractmethod
    def delete_file(self, file_id: str) -> None:
        """Delete a file by its storage identifier."""
        pass
