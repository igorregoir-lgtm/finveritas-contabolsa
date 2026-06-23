"""
Tests for event repository implementations.
"""

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.domain.journal import AccountingEvent, EventType
from src.infrastructure.database import Base, EventRecord
from src.infrastructure.event_repository import InMemoryEventRepository, SQLAlchemyEventRepository


def make_event(event_id: str, previous_hash: str = "GENESIS") -> AccountingEvent:
    return AccountingEvent(
        id=event_id,
        previous_hash=previous_hash,
        timestamp=datetime.now(timezone.utc).isoformat(),
        event_type=EventType.JOURNAL_ENTRY_POSTED,
        payload={"description": "test"},
    )


def test_in_memory_repository_save_and_load():
    repo = InMemoryEventRepository()
    event = make_event("ev-1")
    repo.save_event(event)

    loaded = repo.load_events()
    assert len(loaded) == 1
    assert loaded[0].id == "ev-1"
    assert loaded[0].current_hash == event.current_hash


def test_in_memory_repository_empty():
    repo = InMemoryEventRepository()
    assert repo.load_events() == []


def test_in_memory_repository_multiple_events():
    repo = InMemoryEventRepository()
    first = make_event("ev-1")
    second = make_event("ev-2", previous_hash=first.current_hash)
    repo.save_event(first)
    repo.save_event(second)

    loaded = repo.load_events()
    assert len(loaded) == 2
    assert loaded[1].previous_hash == first.current_hash


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    engine.dispose()


def test_sqlalchemy_repository_save_and_load(db_session):
    repo = SQLAlchemyEventRepository(db_session)
    event = make_event("ev-1")
    repo.save_event(event)

    loaded = repo.load_events()
    assert len(loaded) == 1
    assert loaded[0].id == "ev-1"
    assert loaded[0].current_hash == event.current_hash


def test_sqlalchemy_repository_chain_integrity(db_session):
    repo = SQLAlchemyEventRepository(db_session)
    first = make_event("ev-1")
    second = make_event("ev-2", previous_hash=first.current_hash)
    repo.save_event(first)
    repo.save_event(second)

    loaded = repo.load_events()
    assert len(loaded) == 2
    assert loaded[1].previous_hash == first.current_hash


def test_sqlalchemy_repository_tampering_detected(db_session):
    repo = SQLAlchemyEventRepository(db_session)
    event = make_event("ev-1")
    repo.save_event(event)

    # Tamper with the stored record
    record = db_session.query(EventRecord).first()
    record.current_hash = "tampered"
    db_session.commit()

    with pytest.raises(ValueError, match="tampering"):
        repo.load_events()


def test_sqlalchemy_repository_broken_chain_detected(db_session):
    repo = SQLAlchemyEventRepository(db_session)
    first = make_event("ev-1")
    second = make_event("ev-2", previous_hash=first.current_hash)
    repo.save_event(first)
    repo.save_event(second)

    # Break the previous_hash link of the second record
    record = db_session.query(EventRecord).filter_by(id="ev-2").first()
    record.previous_hash = "broken"
    db_session.commit()

    with pytest.raises(ValueError, match="Hash chain broken"):
        repo.load_events()
