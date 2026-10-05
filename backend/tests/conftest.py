"""Pytest fixtures. Environment variables are set before the app is imported."""

from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

os.environ["APP_ENV"] = "test"
os.environ["SECRET_KEY"] = "test-secret-key-not-for-production"
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["CORS_ORIGINS"] = "http://localhost:5173,http://127.0.0.1:5173"
os.environ["STORAGE_DIR"] = str(Path.cwd() / "storage-test")
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["EXTRACT_ON_UPLOAD"] = "false"
os.environ["EMBEDDING_PROVIDER"] = "test_hash"
os.environ["GENERATION_PROVIDER"] = "mock"
os.environ["CHUNK_SIZE"] = "80"
os.environ["CHUNK_OVERLAP"] = "20"

import pytest
from fastapi.testclient import TestClient

import app.models  # noqa: F401 — register ORM metadata
from app.core.config import clear_settings_cache
from app.db.base import Base
from app.db.session import get_engine, reset_engine
from app.main import app as fastapi_app


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("INDEX_DIR", str(tmp_path / "indexes"))
    clear_settings_cache()
    reset_engine()
    engine = get_engine()
    Base.metadata.create_all(engine)
    with TestClient(fastapi_app) as test_client:
        yield test_client
    Base.metadata.drop_all(engine)
    reset_engine()
    clear_settings_cache()


@pytest.fixture
def register_user(client: TestClient):
    def _register(
        email: str,
        password: str = "correct-horse-battery",
    ) -> dict:
        response = client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password},
        )
        assert response.status_code == 201, response.text
        return response.json()

    return _register
