from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from api.v1.schemas.user_schemas import UserCreate, UserRead
from core.auth import authenticate_user, create_access_token, get_password_hash
from database import get_database
from models.user import User

router = APIRouter()


@router.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_database),
):
    user = await authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.username})

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post("/register", response_model=UserRead)
async def register_user(
    user_create: UserCreate,
    db: AsyncSession = Depends(get_database),
):
    result = await db.execute(select(User).where(User.username == user_create.username))

    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Username is already taken.")

    user = User(
        username=user_create.username,
        email=user_create.email,
        password=get_password_hash(user_create.password),
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user
