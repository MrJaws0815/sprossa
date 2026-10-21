"""Auth-API-Routen: Registrierung, Login, aktueller User (Postgres-persistent)."""
from datetime import datetime, UTC
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.config import settings
from app.repositories.user import UserRepository
from app.schemas.api import UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


# ─── DTOs ─────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ─── POST /auth/register ──────────────────────────────────────────────────

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    existing = await repo.get_by_email(body.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    user = await repo.create_user(
        email=body.email,
        password_hash=hash_password(body.password),
        display_name=body.display_name,
    )
    token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=token)


# ─── POST /auth/login ─────────────────────────────────────────────────────

@router.post("/login")
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    user = await repo.get_by_email(body.email)
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=token)


# ─── GET /auth/me ─────────────────────────────────────────────────────────

@router.get("/me", response_model=UserOut)
async def me(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = UserRepository(db)
    user = await repo.get(UUID(user_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserOut(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        is_active=user.is_active,
        created_at=user.created_at,
    )