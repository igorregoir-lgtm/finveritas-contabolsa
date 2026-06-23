"""In-memory append-only fraud log for demo purposes."""

from typing import List
from ..domain.guardrails.anti_fraud_policy import FraudAttempt, FraudLog


class InMemoryFraudLog(FraudLog):
    def __init__(self):
        self._attempts: List[FraudAttempt] = []

    def append(self, attempt: FraudAttempt) -> None:
        self._attempts.append(attempt)

    def get_all(self) -> List[FraudAttempt]:
        return list(self._attempts)

    def get_blocked(self) -> List[FraudAttempt]:
        return [a for a in self._attempts if a.blocked]
