"""
PostgreSQL + SQLAlchemy setup for FinVeritas persistence.
Stores AccountingEvent as JSON for simplicity (Event Sourcing style).
"""

import os
from sqlalchemy import create_engine, Column, String, DateTime, JSON, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class EventRecord(Base):
    __tablename__ = "accounting_events"

    id = Column(String, primary_key=True)
    previous_hash = Column(String, nullable=False)
    timestamp = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    current_hash = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

_engine = None
_SessionLocal = None

def get_database_url() -> str:
    return os.getenv("DATABASE_URL", "postgresql://finveritas:demo@localhost:5432/finveritas")

def init_db():
    global _engine, _SessionLocal
    db_url = get_database_url()
    _engine = create_engine(db_url, echo=False, pool_pre_ping=True)
    Base.metadata.create_all(_engine)
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    print("Database initialized")

def get_db_session():
    if _SessionLocal is None:
        init_db()
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()
