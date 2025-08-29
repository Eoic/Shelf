from pathlib import Path
import shutil

from core.config import settings
from models.user import User
from services.storage.storage_backend import StorageBackend, StorageFileType


class FileSystemStorage(StorageBackend):
    @property
    def is_local(self) -> bool:
        return True

    def get_prepared_book_dir(self, user: User, book_dir: str) -> Path:
        book_path = settings.BOOK_FILES_DIR / str(user.id) / book_dir
        book_path.mkdir(parents=True, exist_ok=True)
        return book_path

    def get_file(
        self,
        user: User,
        book_dir: str,
        filename: str,
        filetype: StorageFileType,
    ) -> Path | None:
        book_path = self.get_prepared_book_dir(user, book_dir)

        if filetype == StorageFileType.BOOK or filetype == StorageFileType.COVER:
            file_path = book_path / filename
        else:
            return None

        if file_path.exists():
            return file_path

        return None

    def store_file(
        self,
        user: User,
        source: Path,
        book_dir: str,
        filename: str,
        filetype: StorageFileType,
    ) -> Path:
        book_path = self.get_prepared_book_dir(user, book_dir)

        if filetype == StorageFileType.BOOK or filetype == StorageFileType.COVER:
            target_path = book_path / filename
        else:
            raise ValueError()

        shutil.copyfile(str(source), str(target_path))
        return target_path

    def delete_file(
        self,
        user: User,
        book_dir: str,
        filename: str,
        filetype: StorageFileType,
    ) -> bool:
        book_path = self.get_prepared_book_dir(user, book_dir)

        if filetype == StorageFileType.BOOK or filetype == StorageFileType.COVER:
            file_path = book_path / filename
        else:
            return False

        if file_path.exists():
            file_path.unlink()
            return True

        return False
