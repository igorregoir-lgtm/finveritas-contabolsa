"""Domain models for double-entry Journal (Clara Contábil / FinVeritas)."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import List, Optional
import uuid


class AccountType(str, Enum):
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"


@dataclass(frozen=True)
class Account:
    code: str
    name: str
    type: AccountType

    def __post_init__(self):
        if not self.code or not self.name:
            raise ValueError("Account code and name are required")


@dataclass(frozen=True)
class JournalLine:
    account: Account
    debit: Decimal = Decimal("0")
    credit: Decimal = Decimal("0")
    description: str = ""

    def __post_init__(self):
        if self.debit < 0 or self.credit < 0:
            raise ValueError("Debit and credit must be non-negative")
        if self.debit > 0 and self.credit > 0:
            raise ValueError("A line cannot have both debit and credit")


@dataclass(frozen=True)
class JournalEntry:
    id: str
    timestamp: datetime
    description: str
    lines: List[JournalLine]
    source: Optional[str] = None  # e.g. "fiscal_import", "manual", "export"
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.lines:
            raise ValueError("JournalEntry must have at least one line")
        self._validate_balance()

    def _validate_balance(self):
        total_debit = sum(l.debit for l in self.lines)
        total_credit = sum(l.credit for l in self.lines)
        if total_debit != total_credit:
            raise ValueError(
                f"Double-entry violation: debits {total_debit} != credits {total_credit}"
            )
        if total_debit == 0:
            raise ValueError("Entry must have non-zero amount")

    @property
    def total(self) -> Decimal:
        return sum(l.debit for l in self.lines)

    @property
    def is_balanced(self) -> bool:
        return sum(l.debit for l in self.lines) == sum(l.credit for l in self.lines)


class Journal:
    """Append-only double-entry journal."""

    def __init__(self):
        self._entries: List[JournalEntry] = []

    def append(self, entry: JournalEntry) -> None:
        # Idempotency / basic duplicate protection on id
        if any(e.id == entry.id for e in self._entries):
            raise ValueError(f"Duplicate entry id: {entry.id}")
        self._entries.append(entry)

    def get_entries(self, since: Optional[datetime] = None) -> List[JournalEntry]:
        if since is None:
            return list(self._entries)
        return [e for e in self._entries if e.timestamp >= since]

    def trial_balance(self) -> dict[str, Decimal]:
        """Simple trial balance by account code."""
        balances: dict[str, Decimal] = {}
        for entry in self._entries:
            for line in entry.lines:
                code = line.account.code
                balances[code] = balances.get(code, Decimal("0")) + line.debit - line.credit
        return balances

    @property
    def entry_count(self) -> int:
        return len(self._entries)


def create_entry(
    description: str,
    lines: List[JournalLine],
    source: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> JournalEntry:
    """Factory that guarantees a valid, immutable-ish entry."""
    return JournalEntry(
        id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc),
        description=description,
        lines=lines,
        source=source,
        metadata=metadata or {},
    )
