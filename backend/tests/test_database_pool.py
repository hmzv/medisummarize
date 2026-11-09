from sqlalchemy.pool import StaticPool
from app.db.session import create_engine_from_url


def test_file_sqlite_requests_do_not_share_one_connection(tmp_path):
    engine = create_engine_from_url(f"sqlite:///{tmp_path / 'pool-test.db'}")
    try:
        with engine.connect() as first, engine.connect() as second:
            assert first.connection.driver_connection is not second.connection.driver_connection
            assert first.exec_driver_sql("PRAGMA foreign_keys").scalar_one() == 1
    finally:
        engine.dispose()


def test_memory_sqlite_connections_share_the_database():
    engine = create_engine_from_url("sqlite://")
    try:
        assert isinstance(engine.pool, StaticPool)
        with engine.begin() as first:
            first.exec_driver_sql("CREATE TABLE shared (value INTEGER)")
            first.exec_driver_sql("INSERT INTO shared VALUES (7)")
        with engine.connect() as second:
            assert second.exec_driver_sql("SELECT value FROM shared").scalar_one() == 7
    finally:
        engine.dispose()
