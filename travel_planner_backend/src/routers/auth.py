from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.deps import get_current_user
from src.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserPublic
from src.security import create_access_token, hash_password, verify_password
from src.storage.db import get_db_session
from src.storage.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


async def _ensure_demo_user(db: AsyncSession) -> None:
    """Create a demo user if user table is empty."""
    res = await db.execute(select(func.count(User.id)))
    count = int(res.scalar() or 0)
    if count > 0:
        return
    demo = User(email="demo@example.com", password_hash=hash_password("demo123"), full_name="Demo User")
    db.add(demo)
    await db.commit()


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Creates a new local user and returns a bearer token.",
    operation_id="auth_register",
)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db_session)) -> AuthResponse:
    """Register a new local user and return an access token."""
    await _ensure_demo_user(db)

    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(email=payload.email, password_hash=hash_password(payload.password), full_name=payload.full_name)
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token({"user_id": user.id})
    return AuthResponse(access_token=token, user=UserPublic.model_validate(user))


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Login with email and password",
    description="Validates local credentials and returns a bearer token.",
    operation_id="auth_login",
)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db_session)) -> AuthResponse:
    """Login with local credentials and return an access token."""
    await _ensure_demo_user(db)

    res = await db.execute(select(User).where(User.email == payload.email))
    user = res.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token({"user_id": user.id})
    return AuthResponse(access_token=token, user=UserPublic.model_validate(user))


@router.get(
    "/me",
    response_model=UserPublic,
    summary="Get current user",
    description="Returns the current authenticated user.",
    operation_id="auth_me",
)
async def me(current_user: User = Depends(get_current_user)) -> UserPublic:
    """Return current user details."""
    return UserPublic.model_validate(current_user)
