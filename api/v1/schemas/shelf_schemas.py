from pydantic import BaseModel


class ShelfBase(BaseModel):
    name: str


class ShelfCreate(ShelfBase):
    pass


class ShelfRead(ShelfBase):
    id: str
    book_ids: list[str] = []

    class Config:
        from_attributes = True
