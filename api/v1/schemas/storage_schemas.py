from pydantic import BaseModel


class FileStorageConfig(BaseModel):
    pass


class MinIOConfig(BaseModel):
    access_key: str
    secret_key: str
    endpoint: str
    secure: bool = False
