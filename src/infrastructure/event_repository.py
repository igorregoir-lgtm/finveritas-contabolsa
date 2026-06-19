"""
Event Repository for persistence (SQLAlchemy + in-memory fallback)
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from sqlalchemy.orm import Session

from ..domain.journal import AccountingEvent, EventType
from .database import EventRecord

class EventRepository(ABC):
    @abstractmethod
    def save_event(self, event: AccountingEvent):
        pass

    @abstractmethod
    def load_events(self) -> List[AccountingEvent]:
        pass

class InMemoryEventRepository(EventRepository):
    def __init__(self):
        self._events: List[AccountingEvent] = []

    def save_event(self, event: AccountingEvent):
        self._events.append(event)

    def load_events(self) -> List[AccountingEvent]:
        return list(self._events)

class SQLAlchemyEventRepository(EventRepository):
    def __init__(self, db: Session):
        self.db = db

    def save_event(self, event: AccountingEvent):
        record = EventRecord(
            id=event.id,
            previous_hash=event.previous_hash,
            timestamp=event.timestamp,
            event_type=event.event_type.value,
            payload=event.payload,
            current_hash=event.current_hash,
        )
        self.db.add(record)
        self.db.commit()

    def load_events(self) -> List[AccountingEvent]:
        records = self.db.query(EventRecord).order_by(EventRecord.timestamp).all()
        events = []
        for r in records:
            ev = AccountingEvent(
                id=r.id,
                previous_hash=r.previous_hash,
                timestamp=r.timestamp,
                event_type=EventType(r.event_type),
                payload=r.payload,
            )
            # current_hash is computed, but we set it to match
            events.append(ev)
        return events
