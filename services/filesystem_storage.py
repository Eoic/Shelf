from pathlib import Path
import shutil

from core.config import settings
from models.user import User
from services.storage_backend import StorageBackend, StorageFileType


class FileSystemStorage(StorageBackend):
    def get_file(
        self,
        user: User,
        filename: str,
        filetype: StorageFileType,
    ) -> Path | None:
        try:
            parent_path = self._get_parent_path(filetype)
        except ValueError:
            return None

        path = parent_path / str(user.id) / filename

        if path.exists():
            return path

        return None

    def store_file(
        self,
        user: User,
        source: Path,
        filename: str,
        filetype: StorageFileType,
    ) -> Path:
        parent_path = self._get_parent_path(filetype)
        target_path = parent_path / str(user.id) / filename
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(str(source), str(target_path))
        return target_path

    def delete_file(
        self,
        user: User,
        filename: str,
        filetype: StorageFileType,
    ) -> bool:
        try:
            parent_path = self._get_parent_path(filetype)
        except ValueError:
            return False

        path = parent_path / str(user.id) / filename

        if path.exists():
            path.unlink()
            return True

        return False

    def _get_parent_path(self, filetype: StorageFileType) -> Path:
        match filetype:
            case StorageFileType.BOOK:
                return settings.BOOK_FILES_DIR
            case StorageFileType.COVER:
                return settings.COVER_FILES_DIR
            case _:
                raise ValueError()
