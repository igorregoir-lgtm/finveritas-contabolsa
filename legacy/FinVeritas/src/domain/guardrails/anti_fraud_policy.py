"""
Ironclad Anti-Fraud Policy (domain layer).

All sensitive operations MUST go through this policy.
It never mutates state directly — it returns decisions + produces immutable audit records.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Protocol
from enum import Enum


class FraudDecision(str, Enum):
    ALLOW = "allow"
    BLOCK = "block"
    REVIEW = "review"


@dataclass(frozen=True)
class FraudAttempt:
    timestamp: datetime
    actor: str
    action: str
    amount: Optional[Decimal]
    reason: str
    blocked: bool
    metadata: dict = field(default_factory=dict)


@dataclass
class PolicyContext:
    amount: Optional[Decimal] = None
    has_digital_signature: bool = False
    last_action_at: Optional[datetime] = None
    velocity_count: int = 0  # actions in recent window
    source: str = "unknown"
    actor: str = "system"


class FraudLog(Protocol):
    """Append-only log of decisions (infrastructure implements this)."""
    def append(self, attempt: FraudAttempt) -> None: ...


class AntiFraudPolicy:
    """
    Core domain policy for FinVeritas / Clara Contábil.

    Rules (ironclad):
    - Digital signature required for any fiscal import > R$ 0.
    - High value (> R$ 50.000) without signature → immediate BLOCK.
    - Velocity: > 3 high-value actions in 60 minutes → REVIEW or BLOCK.
    - Every decision is recorded (immutable).
    """

    HIGH_VALUE_THRESHOLD = Decimal("50000")
    VELOCITY_WINDOW_MINUTES = 60
    MAX_HIGH_VALUE_PER_WINDOW = 3

    def __init__(self, log: FraudLog):
        self._log = log

    def evaluate(self, context: PolicyContext, action: str) -> FraudDecision:
        reasons: List[str] = []
        decision = FraudDecision.ALLOW

        # Rule 1: Digital signature for fiscal documents
        if action in {"import_pix", "import_nfe", "import_fiscal"}:
            if context.amount and context.amount > 0 and not context.has_digital_signature:
                reasons.append("Missing digital signature on fiscal document")
                decision = FraudDecision.BLOCK

        # Rule 2: High value transactions require signature
        if context.amount and context.amount >= self.HIGH_VALUE_THRESHOLD:
            if not context.has_digital_signature:
                reasons.append(f"High-value transaction (≥ R${self.HIGH_VALUE_THRESHOLD}) requires digital signature")
                decision = FraudDecision.BLOCK

        # Rule 3: Velocity control
        if context.velocity_count > self.MAX_HIGH_VALUE_PER_WINDOW and context.amount and context.amount >= self.HIGH_VALUE_THRESHOLD:
            reasons.append(f"Velocity breach: {context.velocity_count} high-value actions recently")
            decision = FraudDecision.REVIEW if decision != FraudDecision.BLOCK else decision

        blocked = decision == FraudDecision.BLOCK

        attempt = FraudAttempt(
            timestamp=datetime.now(timezone.utc),
            actor=context.actor,
            action=action,
            amount=context.amount,
            reason="; ".join(reasons) if reasons else "Policy passed",
            blocked=blocked,
            metadata={
                "source": context.source,
                "has_signature": context.has_digital_signature,
                "velocity": context.velocity_count,
            },
        )
        self._log.append(attempt)

        return decision

    def is_blocked(self, decision: FraudDecision) -> bool:
        return decision == FraudDecision.BLOCK
