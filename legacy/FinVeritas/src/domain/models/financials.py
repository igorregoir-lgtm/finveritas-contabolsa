"""Financial models and RatioEngine for solvency analysis."""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, List, Optional
from datetime import datetime, timezone

from .journal import Journal, Account, AccountType


@dataclass(frozen=True)
class Ratio:
    name: str
    value: Decimal
    unit: str = ""
    threshold_warning: Optional[Decimal] = None
    threshold_good: Optional[Decimal] = None

    @property
    def status(self) -> str:
        if self.threshold_good is not None and self.value >= self.threshold_good:
            return "good"
        if self.threshold_warning is not None and self.value < self.threshold_warning:
            return "warning"
        return "ok"


@dataclass
class SolvencyReport:
    as_of: datetime
    ratios: List[Ratio]
    credit_score: int  # 0-100
    flags: List[str] = field(default_factory=list)
    recommendation: str = ""
    source_entry_count: int = 0

    def to_dict(self) -> dict:
        return {
            "as_of": self.as_of.isoformat(),
            "credit_score": self.credit_score,
            "ratios": [
                {
                    "name": r.name,
                    "value": str(r.value),
                    "status": r.status,
                }
                for r in self.ratios
            ],
            "flags": self.flags,
            "recommendation": self.recommendation,
        }


class RatioEngine:
    """Pure domain service for calculating financial ratios from Journal data."""

    # Very simplified mapping for demo. In real life this would come from proper
    # balance sheet / income statement aggregation.
    def calculate(
        self,
        journal: Journal,
        current_assets: Decimal = Decimal("0"),
        current_liabilities: Decimal = Decimal("0"),
        total_assets: Decimal = Decimal("0"),
        total_liabilities: Decimal = Decimal("0"),
        equity: Decimal = Decimal("0"),
        ebit: Decimal = Decimal("0"),
        interest_expense: Decimal = Decimal("0"),
    ) -> SolvencyReport:
        """
        Accepts both journal + simplified aggregates (for demo).
        In production this would derive from classified trial balance.
        """
        ratios: List[Ratio] = []
        flags: List[str] = []

        # Current Ratio
        if current_liabilities > 0:
            cr = current_assets / current_liabilities
            ratios.append(
                Ratio(
                    name="Current Ratio",
                    value=round(cr, 2),
                    threshold_warning=Decimal("1.0"),
                    threshold_good=Decimal("1.5"),
                )
            )
            if cr < Decimal("1"):
                flags.append("Current liabilities exceed current assets")

        # Quick Ratio (assume 80% of current assets are quick for demo)
        quick_assets = current_assets * Decimal("0.8")
        if current_liabilities > 0:
            qr = quick_assets / current_liabilities
            ratios.append(
                Ratio(
                    name="Quick Ratio",
                    value=round(qr, 2),
                    threshold_warning=Decimal("0.8"),
                    threshold_good=Decimal("1.0"),
                )
            )

        # Debt to Equity
        if equity > 0:
            dte = total_liabilities / equity
            ratios.append(
                Ratio(
                    name="Debt-to-Equity",
                    value=round(dte, 2),
                    threshold_warning=Decimal("2.0"),
                    threshold_good=Decimal("1.0"),
                )
            )
            if dte > Decimal("3"):
                flags.append("High leverage (Debt/Equity > 3)")

        # Solvency Ratio (Assets / Liabilities)
        if total_liabilities > 0:
            sol = total_assets / total_liabilities
            ratios.append(
                Ratio(
                    name="Solvency Ratio",
                    value=round(sol, 2),
                    threshold_warning=Decimal("1.2"),
                    threshold_good=Decimal("1.5"),
                )
            )

        # Interest Coverage
        if interest_expense > 0:
            ic = ebit / interest_expense
            ratios.append(
                Ratio(
                    name="Interest Coverage",
                    value=round(ic, 1),
                    threshold_warning=Decimal("1.5"),
                    threshold_good=Decimal("3.0"),
                )
            )
            if ic < Decimal("1.5"):
                flags.append("Low interest coverage — earnings risk")

        # Naive credit score (real version would be more sophisticated)
        score = 70
        good_ratios = sum(1 for r in ratios if r.status == "good")
        score += good_ratios * 5
        if flags:
            score -= len(flags) * 8
        score = max(30, min(98, score))  # cap for demo

        recommendation = "Excelente" if score >= 85 else ("Atenção" if score >= 65 else "Alto Risco")

        return SolvencyReport(
            as_of=datetime.now(timezone.utc),
            ratios=ratios,
            credit_score=score,
            flags=flags,
            recommendation=recommendation,
            source_entry_count=journal.entry_count,
        )
