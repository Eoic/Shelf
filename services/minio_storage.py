import logging
from pathlib import Path

from minio import Minio

from core.config import settings
from models.user import User
from services.storage_backend import StorageBackend, StorageFileType

logger = logging.getLogger(__name__)


class MinIOStorage(StorageBackend):
    def __init__(
        self,
        bucket_name: str,
        endpoint: str,
        access_key: str,
        secret_key: str,
        secure: bool = False,
    ):
        self.bucket_name = bucket_name

        self.client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )

    def get_prepared_book_dir(self, user: User, book_dir: str) -> Path:
        return Path(f"books/{user.id}/{book_dir}")

    def get_file(
        self,
        user: User,
        book_dir: str,
        filename: str,
        filetype: StorageFileType,
    ) -> Path | None:
        object_name = self._get_object_name(user, book_dir, filename, filetype)
        local_path = settings.TEMP_FILES_DIR / filename

        try:
            self.client.fget_object(self.bucket_name, object_name, str(local_path))
        except Exception:
            logger.exception("Error retrieving file %s.", object_name)
            return None
        else:
            return local_path

    def store_file(
        self,
        user: User,
        source: Path,
        book_dir: str,
        filename: str,
        filetype: StorageFileType,
    ) -> Path:
        object_name = self._get_object_name(user, book_dir, filename, filetype)

        if not self.client.bucket_exists(self.bucket_name):
            self.client.make_bucket(self.bucket_name)

        self.client.fput_object(self.bucket_name, object_name, str(source))
        return Path(object_name)

    def delete_file(
        self,
        user: User,
        book_dir: str,
        filename: str,
        filetype: StorageFileType,
    ) -> bool:
        object_name = self._get_object_name(user, book_dir, filename, filetype)

        try:
            self.client.remove_object(self.bucket_name, object_name)
        except Exception:
            logger.exception("Error deleting file %s.", object_name)
            return False
        else:
            return True

    def _get_object_name(
        self,
        user: User,
        book_dir: str,
        filename: str,
        filetype: StorageFileType,
    ) -> str:
        prefix = f"books/{user.id}/{book_dir}"

        if filetype == StorageFileType.BOOK or filetype == StorageFileType.COVER:
            return f"{prefix}/{filename}"

        raise ValueError()
