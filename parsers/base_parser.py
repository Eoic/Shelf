from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional, Tuple


class BookParser(ABC):
    @abstractmethod
    def parse_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extracts core metadata from the book file."""
        pass

    @abstractmethod
    def extract_cover_image_data(self, file_path: Path) -> Optional[Tuple[bytes, str]]:
        """
        Extracts the cover image data and its mimetype.
        Returns (image_bytes, mimetype) or None.
        """
        pass

    @staticmethod
    def get_file_format(file_path: Path) -> Optional[str]:
        """Attempt to identify file format based on extension."""
        ext = file_path.suffix.lower()
        if ext == ".epub":
            return "EPUB"
        elif ext == ".pdf":
            return "PDF"
        elif ext in [".mobi", ".azw", ".azw3"]:
            return "MOBI/AZW"  # Group Kindle formats
        # Add more formats as needed
        return None
