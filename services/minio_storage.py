import logging
from pathlib import Path

from minio import Minio

from services.storage_backend import StorageBackend

logger = logging.getLogger(__name__)


class MinIOStorage(StorageBackend):
    def __init__(
        self,
        bucket_name: str,
        endpoint: str,
        access_key: str,
        secret_key: str,
        secure: bool,
    ):
        self.bucket_name = bucket_name

        self.client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )

    def get_file(self, file_id: str) -> Path | None:
        try:
            self.client.fget_object(self.bucket_name, file_id, file_id)
            return Path(file_id)
        except Exception:
            logger.exception("Error retrieving file %s.", file_id)
            return None

    def store_file(self, src_path: Path, dst_name: str) -> str:
        self.client.fput_object(self.bucket_name, dst_name, str(src_path))
        return f"{self.bucket_name}/{dst_name}"

    def delete_file(self, file_id: str):
        self.client.remove_object(self.bucket_name, file_id)
