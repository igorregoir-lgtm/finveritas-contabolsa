"""
Ironclad Anti-Fraud Policy with Hash Chain enforcement
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import List, Protocol

class Decision(str, Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    REVIEW = "REVIEW"

@dataclass
class FraudAttempt:
    timestamp: str
    action: str
    amount: Decimal | None
    decision: Decision
    reason: str
    context: dict

class FraudLog(Protocol):
    def append(self, attempt: FraudAttempt): ...
    def get_all(self) -> List[FraudAttempt]: ...

class AntiFraudPolicy:
    HIGH_VALUE = Decimal("100000")

    def __init__(self, log: FraudLog):
        self.log = log

    def evaluate(self, action: str, amount: Decimal | None, has_signature: bool,
                 chain_valid: bool, velocity_high: bool, actor: str = "system") -> Decision:

        reasons = []

        if not chain_valid:
            reasons.append("Hash chain broken - possible tampering")
            decision = Decision.BLOCK

        elif action in ("post_entry", "import_fiscal") and amount and amount >= self.HIGH_VALUE and not has_signature:
            reasons.append(f"High value (≥ R${self.HIGH_VALUE}) without digital signature")
            decision = Decision.BLOCK

        elif velocity_high and amount and amount >= self.HIGH_VALUE:
            reasons.append("Velocity breach on high-value transactions")
            decision = Decision.REVIEW

        else:
            decision = Decision.ALLOW
            reasons.append("Policy checks passed")

        attempt = FraudAttempt(
            timestamp=datetime.now(timezone.utc).isoformat(),
            action=action,
            amount=amount,
            decision=decision,
            reason="; ".join(reasons),
            context={"has_signature": has_signature, "chain_valid": chain_valid}
        )
        self.log.append(attempt)
        return decision

    def is_blocked(self, decision: Decision) -> bool:
        return decision == Decision.BLOCK
