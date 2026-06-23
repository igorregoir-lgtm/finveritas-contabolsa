"""
Tests for database module setup and defaults.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.infrastructure.database import Base, EventRecord, get_database_url, init_db


def test_database_url_default():
    url = get_database_url()
    assert "postgresql://" in url
    assert "localhost" in url


def test_event_record_creation():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    record = EventRecord(
        id="ev-1",
        previous_hash="GENESIS",
        timestamp="2026-01-01T00:00:00",
        event_type="JOURNAL_ENTRY_POSTED",
        payload={"description": "test"},
        current_hash="a" * 64,
    )
    session.add(record)
    session.commit()

    loaded = session.query(EventRecord).filter_by(id="ev-1").first()
    assert loaded is not None
    assert loaded.current_hash == "a" * 64
    assert loaded.payload["description"] == "test"

    session.close()
    engine.dispose()


def test_init_db_with_sqlite():
    import os

    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    init_db()

    from src.infrastructure import database

    session = database._SessionLocal()
    assert session is not None
    session.close()
    database._engine.dispose()
