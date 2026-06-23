from decimal import Decimal
from src.domain.models.financials import RatioEngine
from src.domain.models.journal import Journal


def test_solvency_report_generation():
    engine = RatioEngine()
    journal = Journal()

    report = engine.calculate(
        journal,
        current_assets=Decimal("180000"),
        current_liabilities=Decimal("72000"),
        total_assets=Decimal("520000"),
        total_liabilities=Decimal("195000"),
        equity=Decimal("325000"),
        ebit=Decimal("42000"),
        interest_expense=Decimal("8500"),
    )

    assert report.credit_score >= 70
    assert any(r.name == "Current Ratio" for r in report.ratios)
    assert report.recommendation in {"Excelente", "Atenção", "Alto Risco"}
