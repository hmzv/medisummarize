"""Alembic baseline can be applied to a throwaway SQLite database."""

from __future__ import annotations

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app.core.config import clear_settings_cache
from app.db.session import reset_engine


def test_alembic_upgrade_head_on_sqlite(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = tmp_path / "segment1.db"
    monkeypatch.setenv("SECRET_KEY", "alembic-test-secret")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    clear_settings_cache()
    reset_engine()

    backend_root = Path(__file__).resolve().parents[1]
    cfg = Config(str(backend_root / "alembic.ini"))
    cfg.set_main_option("script_location", str(backend_root / "migrations"))
    command.upgrade(cfg, "head")

    engine = create_engine(f"sqlite:///{db_path.as_posix()}")
    tables = inspect(engine).get_table_names()
    engine.dispose()
    assert "alembic_version" in tables
    assert "users" in tables
    assert "patient_records" in tables
    assert "documents" in tables
    assert "extracted_pages" in tables
    assert "chunks" in tables
    assert "summaries" in tables

    clear_settings_cache()
    reset_engine()
