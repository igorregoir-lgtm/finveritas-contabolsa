from decimal import Decimal
from datetime import datetime

from src.domain.guardrails.anti_fraud_policy import AntiFraudPolicy, PolicyContext, FraudDecision
from src.infrastructure.fraud_log import InMemoryFraudLog


def test_blocks_missing_signature_on_high_value():
    log = InMemoryFraudLog()
    policy = AntiFraudPolicy(log)

    ctx = PolicyContext(
        amount=Decimal("75000"),
        has_digital_signature=False,
        source="fiscal",
    )
    decision = policy.evaluate(ctx, "import_fiscal")
    assert decision == FraudDecision.BLOCK
    assert len(log.get_blocked()) == 1


def test_allows_signed_high_value():
    log = InMemoryFraudLog()
    policy = AntiFraudPolicy(log)

    ctx = PolicyContext(amount=Decimal("120000"), has_digital_signature=True)
    decision = policy.evaluate(ctx, "import_fiscal")
    assert decision == FraudDecision.ALLOW
