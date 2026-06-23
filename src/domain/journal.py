"""
FinVeritas Journal with Event Sourcing + Hash Chain (immutable)
"""

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional


class EventType(str, Enum):
    JOURNAL_ENTRY_POSTED = "JOURNAL_ENTRY_POSTED"
    ADJUSTMENT_POSTED = "ADJUSTMENT_POSTED"
    FISCAL_IMPORT = "FISCAL_IMPORT"


@dataclass(frozen=True)
class AccountingEvent:
    id: str
    previous_hash: str
    timestamp: str
    event_type: EventType
    payload: Dict[str, Any]
    current_hash: str = field(init=False)

    def __post_init__(self):
        object.__setattr__(self, "current_hash", self._compute_hash())

    def _compute_hash(self) -> str:
        data = {
            "id": self.id,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "event_type": self.event_type.value,
            "payload": self.payload,
        }
        canonical = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()

    def to_dict(self):
        d = asdict(self)
        d["current_hash"] = self.current_hash
        return d


@dataclass
class JournalLine:
    account: str
    debit: Decimal = Decimal(0)
    credit: Decimal = Decimal(0)
    description: str = ""

    def __post_init__(self):
        if self.debit < 0 or self.credit < 0:
            raise ValueError("Debits and credits must be non-negative")


class Journal:
    """Event-sourced immutable journal with hash chain verification."""

    def __init__(self, events: Optional[List[AccountingEvent]] = None):
        self._events: List[AccountingEvent] = events or []
        self._verify_chain_on_load()

    def _verify_chain_on_load(self):
        if not self._events:
            return
        prev = "GENESIS"
        for ev in self._events:
            if ev.previous_hash != prev:
                raise ValueError(f"Hash chain broken at event {ev.id}")
            if ev.current_hash != ev._compute_hash():
                raise ValueError(f"Event hash tampered: {ev.id}")
            prev = ev.current_hash

    @property
    def last_hash(self) -> str:
        return self._events[-1].current_hash if self._events else "GENESIS"

    def post_entry(
        self, description: str, lines: List[JournalLine], source: str = "manual", metadata: Optional[Dict] = None
    ) -> AccountingEvent:
        if not lines:
            raise ValueError("At least one line required")

        total_debit = sum(line.debit for line in lines)
        total_credit = sum(line.credit for line in lines)
        if total_debit != total_credit:
            raise ValueError("Double entry violation: debits != credits")

        payload = {
            "description": description,
            "lines": [asdict(line) for line in lines],
            "total": str(total_debit),
            "source": source,
            "metadata": metadata or {},
        }

        event = AccountingEvent(
            id=str(uuid.uuid4()),
            previous_hash=self.last_hash,
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=EventType.JOURNAL_ENTRY_POSTED,
            payload=payload,
        )
        self._events.append(event)
        return event

    def get_events(self) -> List[AccountingEvent]:
        return list(self._events)

    def get_current_balances(self) -> Dict[str, Decimal]:
        balances: Dict[str, Decimal] = {}
        for ev in self._events:
            for line in ev.payload.get("lines", []):
                acc = line["account"]
                balances[acc] = (
                    balances.get(acc, Decimal(0))
                    + Decimal(str(line.get("debit", 0)))
                    - Decimal(str(line.get("credit", 0)))
                )
        return balances

    def verify_integrity(self) -> bool:
        try:
            self._verify_chain_on_load()
            return True
        except ValueError:
            return False
