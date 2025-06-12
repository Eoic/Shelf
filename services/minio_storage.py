import logging
from pathlib import Path

from storage_backend import StorageBackend

logger = logging.getLogger(__name__)


class MinIOStorage(StorageBackend):
    def __init__(self, client):
        self.client = client

    def store_file(self, src_path: Path, dst_name: str) -> str:
        bucket_name = "your-bucket-name"
        self.client.fput_object(bucket_name, dst_name, str(src_path))
        return f"{bucket_name}/{dst_name}"

    def delete_file(self, file_id: str):
        bucket_name, object_name = file_id.split("/", 1)
        self.client.remove_object(bucket_name, object_name)

    def get_file(self, file_id: str) -> Path | None:
        bucket_name, object_name = file_id.split("/", 1)
        try:
            self.client.fget_object(bucket_name, object_name, object_name)
            return Path(object_name)
        except Exception:
            logger.exception("Error retrieving file %s.", file_id)
            return None
