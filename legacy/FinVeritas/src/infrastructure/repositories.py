"""Simple in-memory repositories for demo."""

from typing import Optional, List
from ..domain.models.journal import Journal, JournalEntry


class InMemoryJournalRepository:
    """Holds a single Journal instance (demo)."""

    def __init__(self):
        self._journal = Journal()

    def get_journal(self) -> Journal:
        return self._journal

    def save_entry(self, entry: JournalEntry) -> None:
        self._journal.append(entry)

    def get_all_entries(self) -> List[JournalEntry]:
        return self._journal.get_entries()
