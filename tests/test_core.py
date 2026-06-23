from decimal import Decimal

from src.domain.journal import Journal, JournalLine
from src.domain.ratio_engine import RatioEngine


def test_journal_double_entry_and_hash_chain():
    j = Journal()
    lines = [JournalLine("Caixa", debit=Decimal("10000")), JournalLine("Receita", credit=Decimal("10000"))]
    ev = j.post_entry("Teste", lines)
    assert j.verify_integrity() is True
    assert ev.current_hash.startswith(ev.current_hash[:10])

def test_ratio_engine_produces_score():
    engine = RatioEngine()
    card = engine.calculate(
        current_assets=Decimal("200000"), current_liabilities=Decimal("80000"),
        inventory=Decimal("50000"), cash=Decimal("40000"),
        total_assets=Decimal("500000"), total_liabilities=Decimal("180000"),
        equity=Decimal("320000"), ebit=Decimal("55000"), ebitda=Decimal("80000"),
        interest_expense=Decimal("8000"), net_debt=Decimal("120000"),
        sales=Decimal("700000"), retained_earnings=Decimal("90000")
    )
    assert 30 <= card.credit_score <= 98
    assert card.overall_status in ("GREEN", "YELLOW", "RED")
