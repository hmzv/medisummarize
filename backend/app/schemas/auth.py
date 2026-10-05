"""Authentication request and response schemas."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import AfterValidator, BaseModel, ConfigDict, Field


def _require_login_email(value: str) -> str:
    normalized = value.strip().lower()
    if len(normalized) > 320:
        raise ValueError("Enter a valid email address.")
    if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
        raise ValueError("Enter a valid email address.")
    local, _, domain = normalized.partition("@")
    if not local or "." not in domain or domain.startswith(".") or domain.endswith("."):
        raise ValueError("Enter a valid email address.")
    if any(part == "" for part in domain.split(".")):
        raise ValueError("Enter a valid email address.")
    return normalized


LoginEmail = Annotated[str, AfterValidator(_require_login_email)]


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: LoginEmail
    password: str = Field(min_length=10, max_length=72)


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: LoginEmail
    password: str = Field(min_length=1, max_length=72)


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    created_at: datetime


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic
