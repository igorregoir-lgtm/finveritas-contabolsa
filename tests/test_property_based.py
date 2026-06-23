"""
Property-based tests for core domain invariants.
"""

from decimal import Decimal

from hypothesis import given, settings
from hypothesis import strategies as st

from src.domain.journal import Journal, JournalLine
from src.domain.ratio_engine import RatioEngine


@settings(max_examples=50)
@given(
    current_assets=st.decimals(min_value=1, max_value=1_000_000, places=2),
    current_liabilities=st.decimals(min_value=1, max_value=500_000, places=2),
    total_assets=st.decimals(min_value=1, max_value=2_000_000, places=2),
    total_liabilities=st.decimals(min_value=1, max_value=1_000_000, places=2),
    ebitda=st.decimals(min_value=1, max_value=500_000, places=2),
    net_debt=st.decimals(min_value=0, max_value=1_000_000, places=2),
)
def test_ratio_engine_produces_valid_card(
    current_assets, current_liabilities, total_assets, total_liabilities, ebitda, net_debt
):
    engine = RatioEngine()
    card = engine.calculate(
        current_assets=current_assets,
        current_liabilities=current_liabilities,
        inventory=Decimal("0"),
        cash=current_assets / Decimal("2"),
        total_assets=total_assets,
        total_liabilities=total_liabilities,
        equity=total_assets - total_liabilities,
        ebit=ebitda,
        ebitda=ebitda,
        interest_expense=Decimal("1"),
        net_debt=net_debt,
        sales=Decimal("1000000"),
        retained_earnings=Decimal("100000"),
    )
    assert isinstance(card.credit_score, int)
    assert 0 <= card.credit_score <= 100
    assert card.overall_status in ("GREEN", "YELLOW", "RED")
    assert len(card.ratios) > 0


@settings(max_examples=30)
@given(
    debits=st.lists(st.decimals(min_value=0, max_value=100_000, places=2), min_size=1, max_size=5),
    credits=st.lists(st.decimals(min_value=0, max_value=100_000, places=2), min_size=1, max_size=5),
)
def test_journal_balanced_entry_preserves_hash_chain(debits, credits):
    total_debit = sum(debits) or Decimal("0")
    total_credit = sum(credits) or Decimal("0")
    if total_debit != total_credit:
        return  # property only applies to balanced entries

    journal = Journal()
    lines = [
        JournalLine(account="cash", debit=total_debit),
        JournalLine(account="revenue", credit=total_credit),
    ]
    event = journal.post_entry("Hypothesis entry", lines)
    assert event.current_hash
    assert journal.verify_integrity()


@settings(max_examples=20)
@given(
    amount=st.decimals(min_value=1, max_value=1_000_000, places=2),
)
def test_journal_post_entry_amount(amount):
    journal = Journal()
    lines = [
        JournalLine(account="cash", debit=amount),
        JournalLine(account="revenue", credit=amount),
    ]
    event = journal.post_entry("Revenue entry", lines)
    assert event.payload["lines"][0]["debit"] == amount
    assert journal.verify_integrity()
