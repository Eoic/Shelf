from typing import Any

from pydantic import BaseModel, ValidationError, field_validator


class FileStorageConfig(BaseModel):
    pass


class MinIOConfig(BaseModel):
    bucket_name: str
    access_key: str
    secret_key: str
    endpoint: str
    secure: bool = False


def parse_config(storage_type: str, value: Any):
    match storage_type:
        case "MINIO":
            return MinIOConfig.model_validate(value)
        case "FILE_SYSTEM":
            return FileStorageConfig.model_validate(value)
        case _:
            raise ValueError


class StorageBase(BaseModel):
    config: MinIOConfig | FileStorageConfig
    storage_type: str

    @field_validator("config", mode="before")
    @classmethod
    def validate_config_by_type(cls, value, info):
        storage_type = info.data.get("storage_type")

        if storage_type is not None and value is not None:
            try:
                return parse_config(storage_type, value)
            except ValidationError as error:
                raise ValueError from error

        return value


class StorageCreate(StorageBase):
    pass


class StorageRead(StorageBase):
    id: int
    is_default: bool = False
    model_config = {"from_attributes": True}


class StorageUpdate(BaseModel):
    config: MinIOConfig | FileStorageConfig | None = None
    storage_type: str | None = None


class PaginatedStorageResponse(BaseModel):
    total: int
    items: list[StorageRead]
