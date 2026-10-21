"""Auth-API-Routen: Registrierung, Login, aktueller User"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from app.core.auth import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.core.dependencies import get_current_user_id
from app.core.config import settings
from app.schemas.api import UserOut

# For now: in-memory user-store (will be replaced by DB in next step)
_USERS: dict[str, dict] = {}

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
async def register(body: RegisterRequest):
    if body.email in _USERS:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user_id = str(UUID(int=len(_USERS) + 1))  # placeholder until DB
    _USERS[body.email] = {
        "id": user_id,
        "email": body.email,
        "password_hash": hash_password(body.password),
        "display_name": body.display_name,
    }
    token = create_access_token(subject=user_id)
    return TokenResponse(access_token=token)


# ─── POST /auth/login ─────────────────────────────────────────────────────

@router.post("/login")
async def login(body: LoginRequest):
    user = _USERS.get(body.email)
    if user is None or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(subject=user["id"])
    return TokenResponse(access_token=token)


# ─── GET /auth/me ─────────────────────────────────────────────────────────

@router.get("/me", response_model=UserOut)
async def me(user_id: str = Depends(get_current_user_id)):
    for u in _USERS.values():
        if u["id"] == user_id:
            return UserOut(
                id=UUID(u["id"]),
                email=u["email"],
                display_name=u["display_name"],
                is_active=True,
                created_at=datetime.now(UTC),
            )
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


from datetime import datetime, UTC