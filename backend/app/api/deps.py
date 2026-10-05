"""Shared FastAPI dependencies."""

from collections.abc import Generator
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import decode_access_token
from app.db.session import get_session_factory
from app.models.user import User
from app.services.auth import get_user_by_id


def get_db() -> Generator[Session, None, None]:
    """Yield a SQLAlchemy session and close it after the request."""
    session_factory = get_session_factory()
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


def _bearer_token(
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    if authorization is None or not authorization.startswith("Bearer "):
        raise AppError(status_code=401, detail="Not authenticated.")
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise AppError(status_code=401, detail="Not authenticated.")
    return token


def get_current_user_id(token: Annotated[str, Depends(_bearer_token)]) -> UUID:
    return decode_access_token(token)


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    user_id: Annotated[UUID, Depends(get_current_user_id)],
) -> User:
    return get_user_by_id(db, user_id)
