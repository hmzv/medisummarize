"""Configuration must fail clearly when required values are missing."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_missing_secret_key_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_missing_database_url_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SECRET_KEY", "unit-test-secret")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_empty_secret_key_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SECRET_KEY", "   ")
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_wildcard_cors_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SECRET_KEY", "unit-test-secret")
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    monkeypatch.setenv("CORS_ORIGINS", "*")
    settings = Settings(_env_file=None)
    with pytest.raises(ValueError, match="Wildcard"):
        _ = settings.cors_origin_list


def test_cors_origins_are_parsed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SECRET_KEY", "unit-test-secret")
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:5173, http://127.0.0.1:5173")
    settings = Settings(_env_file=None)
    assert settings.cors_origin_list == [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
