from pathlib import Path
import shutil
from typing import Optional

from core.config import settings
from services.storage_backend import StorageBackend


class FileSystemStorage(StorageBackend):
    def get_file(self, file_id: str) -> Optional[Path]:
        path = Path(file_id)

        if path.exists():
            return path

        return None

    def store_file(self, src_path: Path, dst_name: str) -> str:
        dst_path = settings.BOOK_FILES_DIR / dst_name
        settings.BOOK_FILES_DIR.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src_path), str(dst_path))
        return str(dst_path)

    def delete_file(self, file_id: str):
        path = Path(file_id)

        if path.exists():
            path.unlink()
