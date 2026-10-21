"""Auth-Kern (Pure Python – keine FastAPI-Abhängigkeit)

Ermöglicht Testen ohne installierte FastAPI/jose/passlib.
"""
from typing import Optional
import hashlib
import base64
import os
import json
import time
import hmac


# ─── Passwort-Hashing (SHA-256 + Salt, ersetzt bcrypt für Tests) ─────────

def hash_password(password: str) -> str:
    """Einfaches Salted-Hash (für Testbarkeit ohne bcrypt installiert).
    In Produktion wird dies durch passlib.bcrypt ersetzt.
    """
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return base64.b64encode(salt + dk).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Verifiziert ein Passwort gegen einen hash_password()-Hash."""
    raw = base64.b64decode(hashed.encode())
    salt = raw[:16]
    expected_dk = raw[16:]
    dk = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt, 100_000)
    return hmac.compare_digest(dk, expected_dk)


# ─── Einfaches JWT (ohne python-jose, HMAC-SHA256) ───────────────────────

_SECRET_KEY = "change-me-in-production"


def encode_jwt(payload: dict, secret: str = _SECRET_KEY) -> str:
    """Erzeugt ein unsigniertes Test-JWT (HMAC-SHA256).
    In Produktion wird dies durch python-jose/jwt ersetzt.
    """
    header = {"alg": "HS256", "typ": "JWT"}
    def _b64(data: str) -> str:
        return base64.urlsafe_b64encode(data.encode()).rstrip(b"=").decode()

    body = _b64(json.dumps(header, separators=(",", ":")))
    payload_str = _b64(json.dumps(payload, separators=(",", ":")))
    signature = hmac.new(
        secret.encode(), f"{body}.{payload_str}".encode(), hashlib.sha256
    ).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).rstrip(b"=").decode()
    return f"{body}.{payload_str}.{sig_b64}"


def decode_jwt(token: str, secret: str = _SECRET_KEY) -> dict:
    """Decodiert ein JWT; wirft ValueError bei ungültiger Signatur."""
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid token format")
    header_b64, payload_b64, sig_b64 = parts

    # Signatur prüfen
    expected_sig = hmac.new(
        secret.encode(), f"{header_b64}.{payload_b64}".encode(), hashlib.sha256
    ).digest()
    actual_sig = base64.urlsafe_b64decode(sig_b64 + "==")
    if not hmac.compare_digest(expected_sig, actual_sig):
        raise ValueError("Invalid signature")

    payload = json.loads(base64.urlsafe_b64decode(payload_b64 + "=="))
    return payload


def create_access_token(subject: str, expires_in_seconds: int = 86400) -> str:
    """Erzeugt ein JWT mit sub und exp.
    
    Args:
        subject: User-ID (UUID als String)
        expires_in_seconds: Gültigkeitsdauer in Sekunden (default 24h)
    """
    payload = {
        "sub": subject,
        "exp": int(time.time()) + expires_in_seconds,
        "iat": int(time.time()),
    }
    return encode_jwt(payload)


def decode_access_token(token: str) -> dict:
    """Decodiert ein JWT; wirft ValueError bei Ablauf oder ungültiger Signatur."""
    payload = decode_jwt(token)
    if payload.get("exp", 0) < time.time():
        raise ValueError("Token expired")
    return payload