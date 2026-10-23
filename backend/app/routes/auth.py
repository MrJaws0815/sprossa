"""Auth-API-Routen: Registrierung, Login, aktueller User, Passwort-Reset (Postgres-persistent)."""
import logging
from datetime import datetime, timedelta, UTC
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Response, status
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
from app.services.email import send_password_reset_email

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


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


# ─── POST /auth/register ──────────────────────────────────────────────────

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, response: Response, db: AsyncSession = Depends(get_db)):
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
    response.set_cookie(
        key="sprossa_token",
        value=token,
        httponly=True,
        secure=False,       # True in Produktion
        samesite="lax",
        max_age=86400,      # 24h
        path="/",
    )
    return TokenResponse(access_token=token)


# ─── POST /auth/login ─────────────────────────────────────────────────────

@router.post("/login")
async def login(body: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    user = await repo.get_by_email(body.email)
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    token = create_access_token(subject=str(user.id))
    response.set_cookie(
        key="sprossa_token",
        value=token,
        httponly=True,
        secure=False,       # True in Produktion
        samesite="lax",
        max_age=86400,      # 24h
        path="/",
    )
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


# ─── POST /auth/forgot-password ──────────────────────────────────────────

log = logging.getLogger("sprossa.auth")


@router.post("/forgot-password")
async def forgot_password(
    body: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Sendet einen Password-Reset-Link, falls die E-Mail existiert.
    Antwortet immer mit 200 (Sicherheit: kein User-Enumeration)."""
    repo = UserRepository(db)
    user = await repo.get_by_email(body.email)
    if user is not None:
        token = str(uuid4())
        expires = datetime.now(UTC) + timedelta(hours=1)
        await repo.update_orm(user.id, reset_token=token, reset_token_expires=expires)
        send_password_reset_email(body.email, token)
    else:
        log.info("Forgot-password für nicht-existente E-Mail: %s", body.email)
    return {"message": "Wenn die E-Mail existiert, erhältst du einen Link zum Zurücksetzen."}


# ─── POST /auth/reset-password ───────────────────────────────────────────


@router.post("/reset-password")
async def reset_password(
    body: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Setzt das Passwort zurück, wenn Token gültig und nicht abgelaufen."""
    repo = UserRepository(db)
    user = await repo.get_by_reset_token(body.token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ungültiger oder abgelaufener Token.",
        )
    if user.reset_token_expires is None or user.reset_token_expires < datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ungültiger oder abgelaufener Token.",
        )
    await repo.update_orm(
        user.id,
        password_hash=hash_password(body.new_password),
        reset_token=None,
        reset_token_expires=None,
    )
    return {"message": "Passwort erfolgreich zurückgesetzt."}


# ─── POST /auth/logout ────────────────────────────────────────────────────


@router.post("/logout")
async def logout(
    response: Response,
    user_id: str = Depends(get_current_user_id),
):
    """Löscht das httpOnly-Cookie sprossa_token."""
    response.set_cookie(
        key="sprossa_token",
        value="",
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=0,      # Cookie sofort löschen
        path="/",
    )
    return {"message": "Logged out"}
