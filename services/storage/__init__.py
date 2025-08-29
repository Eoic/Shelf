"""Utilities for resolving storage backends."""

from models.storage import Storage
from services.storage.exceptions import StorageBackendError
from services.storage.filesystem_storage import FileSystemStorage
from services.storage.minio_storage import MinIOStorage
from services.storage.storage_backend import StorageBackend

STORAGE_BACKENDS: dict[str, type[StorageBackend]] = {
    "FILE_SYSTEM": FileSystemStorage,
    "MINIO": MinIOStorage,
}


def create_storage_backend(storage: Storage | None) -> StorageBackend:
    """Create a :class:`StorageBackend` from a storage model instance.

    Args:
        storage: The storage configuration from the database. ``None``
            results in the default local file system storage.

    Raises:
        StorageBackendError: If the storage type is unknown or misconfigured.
    """

    if storage is None:
        return FileSystemStorage()

    backend_cls = STORAGE_BACKENDS.get(storage.storage_type)

    if backend_cls is None:
        raise StorageBackendError(StorageBackendError.NOT_FOUND)

    if backend_cls is FileSystemStorage:
        return backend_cls()

    # MINIO or other backends requiring config
    config = storage.config or {}

    try:
        return MinIOStorage(
            bucket_name=config["bucket_name"],
            endpoint=config["endpoint"],
            access_key=config["access_key"],
            secret_key=config["secret_key"],
            secure=config.get("secure", False),
        )
    except KeyError as exc:  # pragma: no cover - configuration errors
        raise StorageBackendError(StorageBackendError.NOT_CONFIGURED) from exc
