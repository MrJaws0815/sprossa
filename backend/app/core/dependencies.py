"""FastAPI-Abhängigkeiten (benötigt installierte FastAPI)"""
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.auth import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    request: Request = None,
) -> str:
    """FastAPI-Dependency: extrahiert user_id (UUID as str) aus Bearer-Token oder httpOnly-Cookie."""
    token = None

    # 1. Authorization: Bearer Header (Kompatibilität)
    if credentials is not None:
        token = credentials.credentials

    # 2. Fallback: httpOnly-Cookie sprossa_token
    if token is None:
        token = request.cookies.get("sprossa_token") if request else None

    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        payload = decode_access_token(token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return user_id
