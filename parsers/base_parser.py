from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class BookParser(ABC):
    @abstractmethod
    def parse_metadata(self, file_path: Path) -> dict[str, Any]:
        """Extracts core metadata from the book file."""
        pass

    @abstractmethod
    def extract_cover_image_data(self, file_path: Path) -> tuple[bytes, str] | None:
        """
        Extracts the cover image data and its mimetype.
        Returns (image_bytes, mimetype) or None.
        """
        pass

    @staticmethod
    def get_file_format(file_path: Path) -> str | None:
        """Attempt to identify file format based on extension."""
        extension = file_path.suffix.lower()

        match extension:
            case ".epub":
                return "EPUB"
            case ".pdf":
                return "PDF"
            case ".mobi" | ".azw" | ".azw3":
                return "MOBI/AZW"
            case _:
                return None
