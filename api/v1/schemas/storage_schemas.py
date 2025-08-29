from typing import Any

from pydantic import BaseModel, field_validator, ValidationError


class UnsupportedStorageTypeError(ValueError):
    def __init__(self, storage_type: str):
        supported_types = "MINIO, FILE_SYSTEM"
        super().__init__(f"Unsupported storage type: '{storage_type}'. Supported types are: {supported_types}")


class FileStorageConfig(BaseModel):
    pass


class MinIOConfig(BaseModel):
    bucket_name: str
    access_key: str
    secret_key: str
    endpoint: str
    secure: bool = False


def parse_config(storage_type: str, value: Any):
    match storage_type.upper():
        case "MINIO":
            return MinIOConfig.model_validate(value)
        case "FILE_SYSTEM":
            return FileStorageConfig.model_validate(value)
        case _:
            raise UnsupportedStorageTypeError(storage_type)


class StorageBase(BaseModel):
    title: str | None
    storage_type: str
    config: MinIOConfig | FileStorageConfig

    @field_validator("config", mode="before")
    @classmethod
    def validate_config_by_type(cls, value, info):
        storage_type = info.data.get("storage_type")

        if storage_type is not None and value is not None:
            try:
                return parse_config(storage_type, value)
            except ValidationError as error:
                error_messages = []

                for err in error.errors():
                    field_path = ".".join(str(loc) for loc in err["loc"])
                    error_messages.append(f"{field_path}: {err['msg']}")

                detailed_message = f"Configuration validation failed: {'; '.join(error_messages)}"
                raise ValueError(detailed_message) from error

        return value


class StorageCreate(StorageBase):
    pass


class StorageRead(StorageBase):
    id: str
    is_default: bool = False
    model_config = {"from_attributes": True}


class StorageUpdate(BaseModel):
    title: str | None = None
    config: MinIOConfig | FileStorageConfig | None = None
    storage_type: str | None = None


class PaginatedStorageResponse(BaseModel):
    total: int
    items: list[StorageRead]
