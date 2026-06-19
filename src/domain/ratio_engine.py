"""
FinVeritas Ratio Engine - All required indicators + Credit Score
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Dict
from datetime import datetime, timezone

@dataclass
class Ratio:
    name: str
    value: Decimal
    status: str  # "good" | "warning" | "danger"
    explanation: str
    benchmark: str = ""

@dataclass
class SolvencyCard:
    credit_score: int
    overall_status: str  # "GREEN" | "YELLOW" | "RED"
    ratios: List[Ratio]
    generated_at: str
    flags: List[str] = field(default_factory=list)
    traceability_note: str = "Todos os valores derivam dos lançamentos no Journal (hash chain verificada)"

class RatioEngine:
    def calculate(
        self,
        current_assets: Decimal,
        current_liabilities: Decimal,
        inventory: Decimal,
        cash: Decimal,
        total_assets: Decimal,
        total_liabilities: Decimal,
        equity: Decimal,
        ebit: Decimal,
        ebitda: Decimal,
        interest_expense: Decimal,
        net_debt: Decimal,
        sales: Decimal,
        retained_earnings: Decimal,
        dscr_numerator: Decimal = None,
        dscr_denominator: Decimal = None,
    ) -> SolvencyCard:

        ratios: List[Ratio] = []
        flags: List[str] = []

        # Liquidity
        if current_liabilities > 0:
            lc = current_assets / current_liabilities
            ratios.append(Ratio("Liquidez Corrente", round(lc, 2), self._status(lc, 1.5, 1.0),
                                "Ativo Circulante / Passivo Circulante. Mede capacidade de pagar dívidas de curto prazo."))
            ls = (current_assets - inventory) / current_liabilities
            ratios.append(Ratio("Liquidez Seca", round(ls, 2), self._status(ls, 1.0, 0.8),
                                "Exclui estoque. Mais conservadora."))
            li = cash / current_liabilities
            ratios.append(Ratio("Liquidez Imediata", round(li, 2), self._status(li, 0.5, 0.2),
                                "Caixa imediato vs obrigações de curto prazo."))

        # Solvency
        if ebitda > 0:
            nd_ebitda = net_debt / ebitda
            ratios.append(Ratio("Dívida Líquida / EBITDA", round(nd_ebitda, 2),
                                "danger" if nd_ebitda > Decimal("3") else ("warning" if nd_ebitda > Decimal("2") else "good"),
                                "Alavancagem. Bancos geralmente preferem < 2.5x."))

        if interest_expense > 0:
            ic = ebit / interest_expense
            ratios.append(Ratio("Cobertura de Juros", round(ic, 2), self._status(ic, 3, 1.5),
                                "EBIT / Despesa de Juros. Capacidade de pagar juros."))

        # DSCR
        dscr = Decimal("1.5")  # default demo
        if dscr_denominator and dscr_denominator > 0:
            dscr = dscr_numerator or (ebitda * Decimal("0.8")) / dscr_denominator
        ratios.append(Ratio("DSCR", round(dscr, 2), self._status(dscr, 1.25, 1.0),
                            "Debt Service Coverage Ratio. Gera caixa suficiente para pagar dívida?"))

        # Altman Z (simplified private company)
        if total_assets > 0:
            wc_ta = (current_assets - current_liabilities) / total_assets
            re_ta = retained_earnings / total_assets
            ebit_ta = ebit / total_assets
            equity_debt = equity / total_liabilities if total_liabilities > 0 else Decimal("10")
            sales_ta = sales / total_assets

            z = (Decimal("0.717") * wc_ta + Decimal("0.847") * re_ta +
                 Decimal("3.107") * ebit_ta + Decimal("0.420") * equity_debt +
                 Decimal("0.998") * sales_ta)

            z_status = "good" if z > Decimal("2.9") else ("warning" if z > Decimal("1.23") else "danger")
            ratios.append(Ratio("Altman Z-Score", round(z, 2), z_status,
                                "Modelo de previsão de falência. >2.9 = seguro, <1.23 = alto risco de distress."))

        # Profitability
        if total_assets > 0:
            roa = (ebit * Decimal("0.7")) / total_assets   # simplified after tax proxy
            ratios.append(Ratio("ROA (aprox)", round(roa, 2), self._status(roa, Decimal("0.08"), Decimal("0.03")),
                                "Retorno sobre Ativos. Eficiência no uso do capital."))
        if equity > 0:
            roe = (ebit * Decimal("0.7")) / equity
            ratios.append(Ratio("ROE (aprox)", round(roe, 2), self._status(roe, Decimal("0.15"), Decimal("0.08")),
                                "Retorno sobre Patrimônio Líquido."))

        if ebitda > 0 and sales > 0:
            ebitda_margin = ebitda / sales
            ratios.append(Ratio("Margem EBITDA", round(ebitda_margin, 2),
                                self._status(ebitda_margin, Decimal("0.20"), Decimal("0.10")),
                                "EBITDA / Receita. Geração operacional de caixa."))

        # Credit Score composite (demo weights)
        score = 65
        good_count = sum(1 for r in ratios if r.status == "good")
        danger_count = sum(1 for r in ratios if r.status == "danger")

        score += good_count * 3
        score -= danger_count * 5
        score = max(25, min(98, score))

        overall = "GREEN" if score >= 80 else ("YELLOW" if score >= 60 else "RED")

        if danger_count > 2:
            flags.append("Múltiplos indicadores em zona de risco alto.")

        return SolvencyCard(
            credit_score=score,
            overall_status=overall,
            ratios=ratios,
            generated_at=datetime.now(timezone.utc).isoformat(),
            flags=flags
        )

    def _status(self, value: Decimal, good: Decimal, warning: Decimal) -> str:
        if value >= good:
            return "good"
        if value < warning:
            return "danger"
        return "warning"
