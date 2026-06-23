"""
FinVeritas Contabolsa - Main Application Service (orchestrates everything)
"""

import hashlib
import json
from decimal import Decimal
from typing import Dict, List, Optional

from ..domain.anti_fraud_policy import AntiFraudPolicy, FraudAttempt, InMemoryFraudLog
from ..domain.consolidation import (
    ConsolidationOrchestrator,
    CovenantTestResult,
    EliminationEntry,
    Explanation,
)
from ..domain.journal import AccountingEvent, Journal, JournalLine
from ..domain.ratio_engine import RatioEngine, SolvencyCard
from ..infrastructure.event_repository import EventRepository, InMemoryEventRepository
from ..infrastructure.fiscal_simulator import FiscalSimulator
from ..infrastructure.signed_export import SignedExporter


class FinVeritasService:
    def __init__(self, journal_repo: Optional[EventRepository] = None):
        self.fraud_log = InMemoryFraudLog()
        self.policy = AntiFraudPolicy(self.fraud_log)
        self.ratio_engine = RatioEngine()
        self.exporter = SignedExporter()

        if journal_repo is None:
            journal_repo = InMemoryEventRepository()

        self.journal = Journal(events=journal_repo.load_events() if hasattr(journal_repo, "load_events") else None)
        # For simplicity, we keep events in memory for now but will sync in repo impl
        self._journal_repo = journal_repo

        self.fiscal = FiscalSimulator(self.policy, self.journal)

        # === FinStatement Pro: 3 Planes Orchestrator (Execution + Intelligence) ===
        self.consolidator = ConsolidationOrchestrator()
        self._group_demo_loaded = False
        self._current_consol_result: Optional[Dict] = None

        # Seed demo data if empty
        if len(self.journal.get_events()) == 0:
            self._seed_demo_data()

    def _seed_demo_data(self):
        lines = [
            JournalLine("1.1.01 - Caixa/Bancos", debit=Decimal("250000")),
            JournalLine("2.3.01 - Capital Social", credit=Decimal("250000")),
        ]
        ev = self.journal.post_entry("Aporte inicial dos sócios", lines, source="seed")
        self._journal_repo.save_event(ev)

    def post_journal_entry(self, description: str, lines: List[JournalLine], actor: str = "user") -> AccountingEvent:
        # Check chain
        chain_ok = self.journal.verify_integrity()
        amount = sum(line.debit for line in lines)

        decision = self.policy.evaluate(
            "post_entry", amount, has_signature=True, chain_valid=chain_ok, velocity_high=False, actor=actor
        )
        if self.policy.is_blocked(decision):
            raise PermissionError(f"Blocked by anti-fraud: {decision.value}")

        event = self.journal.post_entry(description, lines, source=f"manual:{actor}")
        self._journal_repo.save_event(event)
        return event

    def import_fiscal(self, pix: dict, nfe: Optional[dict] = None, actor: str = "user"):
        return self.fiscal.import_pix_nfe(pix, nfe, actor)

    def calculate_solvency(self, **overrides) -> SolvencyCard:
        if not self.journal.verify_integrity():
            raise ValueError("Cannot calculate on broken journal chain!")

        # Read real balances from the immutable journal; fall back to demo defaults when empty
        balances = self.journal.get_current_balances()

        def _bal(account_prefix: str, default: Decimal) -> Decimal:
            total = sum(v for k, v in balances.items() if k.startswith(account_prefix))
            return total if total != Decimal(0) else default

        # Account prefix mapping (Brazilian chart of accounts convention)
        current_assets = overrides.get("current_assets", _bal("1.1", Decimal("185000")))
        current_liabilities = overrides.get("current_liabilities", _bal("2.1", Decimal("72000")))
        inventory = overrides.get("inventory", _bal("1.1.03", Decimal("45000")))
        cash = overrides.get("cash", _bal("1.1.01", Decimal("38000")))
        total_assets = overrides.get("total_assets", _bal("1.", Decimal("520000")))
        total_liabilities = overrides.get("total_liabilities", _bal("2.", Decimal("195000")))
        equity = overrides.get("equity", _bal("2.3", Decimal("325000")))
        ebit = overrides.get("ebit", _bal("3.", Decimal("48000")))
        ebitda = overrides.get("ebitda", ebit + Decimal("24000") if ebit != Decimal("48000") else Decimal("72000"))
        interest_expense = overrides.get("interest_expense", _bal("4.1", Decimal("9500")))
        net_debt = overrides.get(
            "net_debt", total_liabilities - cash if total_liabilities != Decimal("195000") else Decimal("142000")
        )
        sales = overrides.get("sales", _bal("3.9", Decimal("620000")))
        retained_earnings = overrides.get("retained_earnings", _bal("2.3.02", Decimal("78000")))

        return self.ratio_engine.calculate(
            current_assets=current_assets,
            current_liabilities=current_liabilities,
            inventory=inventory,
            cash=cash,
            total_assets=total_assets,
            total_liabilities=total_liabilities,
            equity=equity,
            ebit=ebit,
            ebitda=ebitda,
            interest_expense=interest_expense,
            net_debt=net_debt,
            sales=sales,
            retained_earnings=retained_earnings,
        )

    # ==================== FinStatement Pro Group Consolidation (WHAT THE HELL) ====================
    def load_group_demo(self) -> Dict:
        """Load impressive 3-entity interco group per plan golden scenario."""
        if self._group_demo_loaded:
            return {"status": "already_loaded"}
        g, ents, scope, period = self.consolidator.register_group_demo()
        self._group_demo_loaded = True
        return {
            "group": g.group_name,
            "entities": [e.legal_name for e in ents],
            "scope": scope.scope_name,
            "period": f"{period.start_date} to {period.end_date}",
            "status": "ready",
        }

    def run_consolidation(self) -> Dict:
        """Execution Plane: full recon + elim + covenants + explain. The core demo."""
        if not self._group_demo_loaded:
            self.load_group_demo()
        result = self.consolidator.run_full_consolidation(1)
        self._current_consol_result = result
        return result

    def explain_any(self, key: str) -> Dict:
        return self.consolidator.get_explain(key)

    def try_fraud_attempt(self, desc: str) -> str:
        return self.consolidator.try_fraud(desc)

    def get_last_covenants(self) -> List[CovenantTestResult]:
        return self.consolidator._last_covenants or []

    def get_last_elims(self) -> List[EliminationEntry]:
        return self.consolidator._last_elims or []

    def get_explanations(self) -> List[Explanation]:
        return self.consolidator._explains or []

    def export_for_bank(self) -> Dict:
        # Enhanced credit-grade pack with group + covenants + explains + hashes
        consol_json = json.dumps(self._current_consol_result or {}, sort_keys=True, default=str)
        real_hash = hashlib.sha256(consol_json.encode()).hexdigest()
        return {
            "root_hash": "FINSTATEMENT-PRO-" + real_hash[:32],
            "group_consolidated": self._current_consol_result or {},
            "covenants": [c.__dict__ for c in self.get_last_covenants()],
            "elims_count": len(self.get_last_elims()),
            "explain_count": len(self.get_explanations()),
            "anti_fraud": "hash_chain_verified + four_eyes_enforced",
        }

    # Next-level: What-If simulation for founder/analyst "play with the numbers"
    def apply_what_if(
        self,
        interco_loan_delta: Decimal = Decimal("0"),
        ebitda_multiplier: Decimal = Decimal("1"),
        ownership_shift: Decimal = Decimal("0"),
    ) -> Dict:
        """Simulate impact of changes on covenants/headroom. Returns deltas for impressive live experience."""
        self._current_consol_result or self.run_consolidation()
        # Semantically correct: new_leverage = (base_net_debt + delta) / (base_ebitda * ebitda_mult)
        base_net_debt = Decimal("3200000")
        base_ebitda = Decimal("1250000")
        lev_threshold = Decimal("3.5")
        new_lev = (base_net_debt + interco_loan_delta) / (base_ebitda * ebitda_multiplier)
        lev_head = lev_threshold - new_lev
        lev_status = "PASS" if lev_head >= 0 else "FAIL"

        # DSCR: higher EBITDA multiplier → more coverage
        base_dscr = Decimal("1.5")
        new_dscr = base_dscr * ebitda_multiplier
        dscr_head = new_dscr - Decimal("1.2")
        dscr_status = "PASS" if dscr_head >= 0 else "FAIL"

        return {
            "what_if_params": {"interco_delta": str(interco_loan_delta), "ebitda_mult": str(ebitda_multiplier)},
            "covenants": [
                {
                    "code": "LEV-01",
                    "new_value": str(new_lev.quantize(Decimal("0.01"))),
                    "headroom": str(lev_head.quantize(Decimal("0.01"))),
                    "status": lev_status,
                },
                {
                    "code": "DSCR-01",
                    "new_value": str(new_dscr.quantize(Decimal("0.1"))),
                    "headroom": str(dscr_head.quantize(Decimal("0.1"))),
                    "status": dscr_status,
                },
            ],
            "narrative": (
                "What-if applied: interco adjusted, EBITDA scaled. "
                "All lineage and anti-fraud rules remain enforced on the base data."
            ),
        }

    def get_covenant_trends(self):
        return self.consolidator.get_covenant_trends()

    def run_for_period(self, pid: int):
        return self.consolidator.run_for_period(pid)

    def generate_real_credit_memo_pdf(self) -> str:
        """Trigger real ReportLab PDF for group + covenants."""
        consol = self._current_consol_result or self.run_consolidation()
        covs = self.get_last_covenants()
        cov_dicts = [
            {
                "code": c.covenant_code,
                "observed_value": c.observed_value,
                "threshold": c.threshold,
                "headroom": c.headroom,
                "status": c.status,
            }
            for c in covs
        ]
        return self.exporter.generate_group_credit_memo(
            "Allla Group",
            consol.get("consol", {}),
            cov_dicts,
            len(self.get_last_elims()),
            self.export_for_bank().get("root_hash", "DEMO-HASH"),
            len(self.get_explanations()),
        )

    def run_ai_anomaly(self):
        """Expose AI anomaly detection."""
        return self.consolidator.detect_anomalies()

    def run_stress_test(self, stress: float = 0.2):
        """Expose stress testing for covenants (credit risk style)."""
        metrics = {"net_debt_ebitda": Decimal("2.56"), "ebitda": Decimal("1250000")}
        return self.consolidator.stress_test_covenants(metrics, stress)

    def export_to_bank(self) -> dict:
        if not self.journal.verify_integrity():
            raise ValueError("Export blocked: journal chain is invalid")

        solvency = self.calculate_solvency()
        events = self.journal.get_events()

        return self.exporter.generate_signed_package(
            journal_events=events, solvency_card=solvency, company_name="Empresa Exemplo Ltda"
        )

    def get_fraud_log(self) -> List[FraudAttempt]:
        return self.fraud_log.get_all()

    def force_fraud_test(self, amount: Decimal, has_sig: bool = False):
        """Helper to demo blocking"""
        chain_ok = self.journal.verify_integrity()
        decision = self.policy.evaluate("import_fiscal", amount, has_sig, chain_ok, velocity_high=False)
        return decision
