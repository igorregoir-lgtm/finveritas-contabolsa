"""
FinVeritas Contabolsa - Main Application Service (orchestrates everything)
"""

from decimal import Decimal
from typing import List, Optional, Tuple
from ..domain.journal import Journal, JournalLine, AccountingEvent, EventType
from ..domain.ratio_engine import RatioEngine, SolvencyCard
from ..domain.anti_fraud_policy import AntiFraudPolicy, Decision, FraudAttempt
from ..infrastructure.fiscal_simulator import FiscalSimulator
from ..infrastructure.signed_export import SignedExporter
from ..infrastructure.event_repository import EventRepository, InMemoryEventRepository
from ..infrastructure.event_repository import EventRepository, InMemoryEventRepository

class InMemoryFraudLog:
    def __init__(self):
        self.attempts: List[FraudAttempt] = []
    def append(self, a): self.attempts.append(a)
    def get_all(self): return list(self.attempts)

class FinVeritasService:
    def __init__(self, journal_repo: Optional[EventRepository] = None):
        self.fraud_log = InMemoryFraudLog()
        self.policy = AntiFraudPolicy(self.fraud_log)
        self.ratio_engine = RatioEngine()
        self.exporter = SignedExporter()

        if journal_repo is None:
            journal_repo = InMemoryEventRepository()

        self.journal = Journal(events=journal_repo.load_events() if hasattr(journal_repo, 'load_events') else None)
        # For simplicity, we keep events in memory for now but will sync in repo impl
        self._journal_repo = journal_repo

        self.fiscal = FiscalSimulator(self.policy, self.journal)

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
        amount = sum(l.debit for l in lines)

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

        # Use realistic demo numbers + current balances if available
        return self.ratio_engine.calculate(
            current_assets=overrides.get("current_assets", Decimal("185000")),
            current_liabilities=overrides.get("current_liabilities", Decimal("72000")),
            inventory=overrides.get("inventory", Decimal("45000")),
            cash=overrides.get("cash", Decimal("38000")),
            total_assets=overrides.get("total_assets", Decimal("520000")),
            total_liabilities=overrides.get("total_liabilities", Decimal("195000")),
            equity=overrides.get("equity", Decimal("325000")),
            ebit=overrides.get("ebit", Decimal("48000")),
            ebitda=overrides.get("ebitda", Decimal("72000")),
            interest_expense=overrides.get("interest_expense", Decimal("9500")),
            net_debt=overrides.get("net_debt", Decimal("142000")),
            sales=overrides.get("sales", Decimal("620000")),
            retained_earnings=overrides.get("retained_earnings", Decimal("78000")),
        )

    def export_to_bank(self) -> dict:
        if not self.journal.verify_integrity():
            raise ValueError("Export blocked: journal chain is invalid")

        solvency = self.calculate_solvency()
        events = self.journal.get_events()

        return self.exporter.generate_signed_package(
            journal_events=events,
            solvency_card=solvency,
            company_name="Empresa Exemplo Ltda"
        )

    def get_fraud_log(self) -> List[FraudAttempt]:
        return self.fraud_log.get_all()

    def force_fraud_test(self, amount: Decimal, has_sig: bool = False):
        """Helper to demo blocking"""
        chain_ok = self.journal.verify_integrity()
        decision = self.policy.evaluate("import_fiscal", amount, has_sig, chain_ok, velocity_high=False)
        return decision
