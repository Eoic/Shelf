from typing import Literal

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserRead(BaseModel):
    username: str
    email: EmailStr
    preferences: dict

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str
    password: str


class UserPreferencesUpdate(BaseModel):
    storage_backend: Literal["filesystem", "s3", "gdrive"]
