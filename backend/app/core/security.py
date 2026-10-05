"""Password hashing and JWT access tokens.

This prototype uses bcrypt (not a hand-rolled hash) and PyJWT HS256.
Tokens are sent in the Authorization header, never in URLs.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from jwt import InvalidTokenError

from app.core.config import get_settings
from app.core.errors import AppError

BCRYPT_MAX_BYTES = 72


def hash_password(password: str) -> str:
    """Hash a password with bcrypt. Test env uses fewer rounds for speed."""
    password_bytes = _password_bytes(password)
    rounds = 4 if get_settings().environment == "test" else 12
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=rounds))
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        password_bytes = _password_bytes(password)
        return bcrypt.checkpw(password_bytes, password_hash.encode("utf-8"))
    except (ValueError, AppError):
        return False


def _password_bytes(password: str) -> bytes:
    encoded = password.encode("utf-8")
    if len(encoded) > BCRYPT_MAX_BYTES:
        raise AppError(status_code=422, detail="Password is too long.")
    return encoded


def create_access_token(
    user_id: uuid.UUID,
    email: str,
    expires_delta: timedelta | None = None,
) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expire = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload = {
        "sub": str(user_id),
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "typ": "access",
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> uuid.UUID:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except InvalidTokenError as exc:
        raise AppError(status_code=401, detail="Invalid or expired token.") from exc
    if payload.get("typ") != "access":
        raise AppError(status_code=401, detail="Invalid or expired token.")
    subject = payload.get("sub")
    if not subject:
        raise AppError(status_code=401, detail="Invalid or expired token.")
    try:
        return uuid.UUID(str(subject))
    except ValueError as exc:
        raise AppError(status_code=401, detail="Invalid or expired token.") from exc
