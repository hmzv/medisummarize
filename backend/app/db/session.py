"""SQLAlchemy engine and session factory."""

from collections.abc import Callable

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings

_engine: Engine | None = None
_session_factory: Callable[[], Session] | None = None


def _enable_sqlite_foreign_keys(engine: Engine) -> None:
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _connection_record) -> None:  # type: ignore[no-untyped-def]
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def create_engine_from_url(url: str) -> Engine:
    """Share memory databases, but give file databases separate pooled connections."""
    if url.startswith("sqlite"):
        database = make_url(url).database
        memory_database = not database or database == ":memory:" or make_url(url).query.get("mode") == "memory"
        engine = create_engine(
            url,
            connect_args={"check_same_thread": False},
            **({"poolclass": StaticPool} if memory_database else {}),
        )
        _enable_sqlite_foreign_keys(engine)
        return engine
    return create_engine(url, pool_pre_ping=True)


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine_from_url(get_settings().database_url)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)
    return _session_factory


def reset_engine() -> None:
    """Test helper to dispose and recreate the engine after settings change."""
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None
