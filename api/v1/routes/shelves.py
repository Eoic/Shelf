from fastapi import APIRouter, Depends, Security

from api.v1.schemas.shelf_schemas import ShelfCreate, ShelfRead
from core.auth import get_current_user
from models.user import User
from services.book_service import BookService, get_book_service
from services.shelf_service import ShelfService, get_shelf_service

router = APIRouter()


@router.post(
    "/",
    response_model=ShelfRead,
    status_code=201,
    summary="Create a new shelf",
)
async def create_shelf(
    shelf: ShelfCreate,
    shelf_service: ShelfService = Depends(get_shelf_service),
    user: User = Security(get_current_user),
):
    created = await shelf_service.create_shelf(user.id, shelf.name)
    return ShelfRead(id=created.id, name=created.name, book_ids=[b.id for b in created.books])


@router.get("/", response_model=list[ShelfRead], summary="List shelves")
async def list_shelves(
    shelf_service: ShelfService = Depends(get_shelf_service),
    user: User = Security(get_current_user),
):
    shelves = await shelf_service.list_shelves(user.id)
    return [
        ShelfRead(id=s.id, name=s.name, book_ids=[b.id for b in s.books])
        for s in shelves
    ]


@router.get(
    "/{shelf_id}", response_model=ShelfRead, summary="Retrieve a shelf",
)
async def get_shelf(
    shelf_id: str,
    shelf_service: ShelfService = Depends(get_shelf_service),
    user: User = Security(get_current_user),
):
    shelf = await shelf_service.get_shelf(shelf_id, user.id)
    return ShelfRead(id=shelf.id, name=shelf.name, book_ids=[b.id for b in shelf.books])


@router.delete("/{shelf_id}", status_code=204, summary="Delete a shelf")
async def delete_shelf(
    shelf_id: str,
    shelf_service: ShelfService = Depends(get_shelf_service),
    user: User = Security(get_current_user),
):
    await shelf_service.delete_shelf(shelf_id, user.id)
    return


@router.post(
    "/{shelf_id}/books/{book_id}",
    response_model=ShelfRead,
    summary="Add a book to a shelf",
)
async def add_book_to_shelf(
    shelf_id: str,
    book_id: str,
    shelf_service: ShelfService = Depends(get_shelf_service),
    book_service: BookService = Depends(get_book_service),
    user: User = Security(get_current_user),
):
    book = await book_service.get_book_by_id(book_id, user.id, raw=True)
    shelf = await shelf_service.add_book(shelf_id, book, user.id)
    return ShelfRead(id=shelf.id, name=shelf.name, book_ids=[b.id for b in shelf.books])


@router.delete(
    "/{shelf_id}/books/{book_id}", status_code=204, summary="Remove a book from a shelf",
)
async def remove_book_from_shelf(
    shelf_id: str,
    book_id: str,
    shelf_service: ShelfService = Depends(get_shelf_service),
    book_service: BookService = Depends(get_book_service),
    user: User = Security(get_current_user),
):
    book = await book_service.get_book_by_id(book_id, user.id, raw=True)
    await shelf_service.remove_book(shelf_id, book, user.id)
    return
