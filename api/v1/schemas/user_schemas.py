from pydantic import BaseModel, EmailStr


class Preferences(BaseModel):
    theme: str | None = None


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserRead(BaseModel):
    username: str
    email: EmailStr
    preferences: Preferences

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str
    password: str


class UserPreferencesUpdate(Preferences):
    class Config:
        from_attributes = True
        extra = "forbid"
        validate_by_name = True
