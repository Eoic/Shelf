from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_database, shelf_crud
from models.book import Book
from models.shelf import Shelf


class ShelfService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_shelf(self, user_id: str, name: str) -> Shelf:
        return await shelf_crud.create_shelf(self.db, user_id, name)

    async def list_shelves(self, user_id: str) -> list[Shelf]:
        return await shelf_crud.get_shelves(self.db, user_id)

    async def get_shelf(self, shelf_id: str, user_id: str) -> Shelf:
        shelf = await shelf_crud.get_shelf(self.db, shelf_id, user_id)
        if not shelf:
            raise HTTPException(status_code=404, detail="Shelf not found.")
        return shelf

    async def delete_shelf(self, shelf_id: str, user_id: str) -> None:
        shelf = await self.get_shelf(shelf_id, user_id)
        await shelf_crud.delete_shelf(self.db, shelf)

    async def add_book(self, shelf_id: str, book: Book, user_id: str) -> Shelf:
        shelf = await self.get_shelf(shelf_id, user_id)

        if book in shelf.books:
            raise HTTPException(status_code=400, detail="Book already on shelf.")

        return await shelf_crud.add_book(self.db, shelf, book)

    async def remove_book(self, shelf_id: str, book: Book, user_id: str) -> Shelf:
        shelf = await self.get_shelf(shelf_id, user_id)

        if book not in shelf.books:
            raise HTTPException(status_code=404, detail="Book not on shelf.")

        return await shelf_crud.remove_book(self.db, shelf, book)


def get_shelf_service(database: AsyncSession = Depends(get_database)) -> ShelfService:
    return ShelfService(database)
