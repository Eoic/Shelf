import hashlib
import secrets

from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import or_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from api.v1.schemas.user_schemas import (
    APIKeyResponse,
    UserCreate,
    UserPreferencesUpdate,
    UserRead,
)
from core.auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    get_password_hash,
)
from core.crockford import generate_crockford_id
from database import get_database
from models.user import User

router = APIRouter()


@router.post(
    "/token",
    summary="Login and get access token",
)
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


@router.post(
    "/register",
    response_model=UserRead,
    summary="Register a new user",
)
async def register_user(
    user_create: UserCreate,
    db: AsyncSession = Depends(get_database),
):
    result = await db.execute(
        select(User).where(
            or_(
                User.username == user_create.username,
                User.email == user_create.email,
            ),
        ),
    )

    if result.scalars().first():
        raise HTTPException(
            status_code=400,
            detail="Username or email is already taken.",
        )

    user = User(
        id=generate_crockford_id(),
        username=user_create.username,
        email=user_create.email,
        password=get_password_hash(user_create.password),
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get current user details",
)
async def read_current_user(current_user: User = Security(get_current_user)):
    return current_user


@router.put(
    "/preferences",
    response_model=UserRead,
    summary="Update user preferences",
)
async def update_user_preferences(
    preferences_update: UserPreferencesUpdate,
    db: AsyncSession = Depends(get_database),
    current_user: User = Security(get_current_user),
):
    current_preferences = current_user.preferences if isinstance(current_user.preferences, dict) else {}

    new_preferences = {
        **current_preferences,
        **preferences_update.model_dump(exclude_unset=True),
    }

    query = (
        update(User)
        .where(User.id == current_user.id)
        .values(preferences=new_preferences)
        .execution_options(synchronize_session="fetch")
    )

    await db.execute(query)
    await db.commit()
    await db.refresh(current_user)

    return current_user


@router.post(
    "/api-key",
    response_model=APIKeyResponse,
    summary="Generate a new API key",
)
async def generate_api_key(
    db: AsyncSession = Depends(get_database),
    current_user: User = Security(get_current_user),
):
    key = secrets.token_urlsafe(32)
    hashed = hashlib.sha256(key.encode()).hexdigest()
    current_user.api_key_hash = hashed
    await db.commit()
    return APIKeyResponse(api_key=key)
