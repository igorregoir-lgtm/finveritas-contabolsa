"""Application use cases / orchestration layer for FinVeritas."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List

from ..domain.models.journal import JournalEntry, Journal, create_entry, JournalLine, Account, AccountType
from ..domain.models.financials import RatioEngine, SolvencyReport
from ..domain.guardrails.anti_fraud_policy import AntiFraudPolicy, PolicyContext
from ..infrastructure.repositories import InMemoryJournalRepository
from ..infrastructure.fiscal_integrator import FiscalIntegrator
from ..infrastructure.bank_exporter import BankExporter, BankPackage
from ..infrastructure.fraud_log import InMemoryFraudLog


class FinVeritasService:
    """
    Facade / Application Service that wires the real modules.

    UI (Streamlit or future frontend) should call these methods.
    """

    def __init__(self):
        self._fraud_log = InMemoryFraudLog()
        self._fraud_policy = AntiFraudPolicy(self._fraud_log)
        self._journal_repo = InMemoryJournalRepository()
        self._fiscal = FiscalIntegrator(self._fraud_policy)
        self._bank_exporter = BankExporter()
        self._ratio_engine = RatioEngine()

    # --- Journal ---
    def post_manual_entry(
        self,
        description: str,
        debit_account_code: str,
        credit_account_code: str,
        amount: Decimal,
        actor: str = "user",
    ) -> JournalEntry:
        # Very simple accounts for demo
        accounts = {
            "1.1.01": Account("1.1.01", "Caixa/Banco", AccountType.ASSET),
            "3.1.01": Account("3.1.01", "Receita", AccountType.REVENUE),
            "2.1.01": Account("2.1.01", "Fornecedores", AccountType.LIABILITY),
            "4.1.01": Account("4.1.01", "Despesa Operacional", AccountType.EXPENSE),
        }

        dr = accounts.get(debit_account_code, Account(debit_account_code, "Conta Débito", AccountType.ASSET))
        cr = accounts.get(credit_account_code, Account(credit_account_code, "Conta Crédito", AccountType.REVENUE))

        lines = [
            JournalLine(account=dr, debit=amount),
            JournalLine(account=cr, credit=amount),
        ]
        entry = create_entry(description, lines, source="manual", metadata={"actor": actor})

        # Guard high value manual entries
        ctx = PolicyContext(amount=amount, has_digital_signature=True, actor=actor, source="manual")
        decision = self._fraud_policy.evaluate(ctx, "manual_journal")
        if self._fraud_policy.is_blocked(decision):
            raise PermissionError("High value manual entry blocked by policy")

        self._journal_repo.save_entry(entry)
        return entry

    def get_journal(self) -> Journal:
        return self._journal_repo.get_journal()

    # --- Fiscal ---
    def import_fiscal(
        self,
        pix_data: dict,
        nfe_data: Optional[dict] = None,
        actor: str = "user",
    ):
        reconciled, journal_entry = self._fiscal.importar_pix_nfe(pix_data, nfe_data, actor=actor)
        if journal_entry:
            self._journal_repo.save_entry(journal_entry)
        return reconciled, journal_entry

    # --- Ratios / Solvency ---
    def calculate_solvency(
        self,
        current_assets: Decimal = Decimal("120000"),
        current_liabilities: Decimal = Decimal("65000"),
        total_assets: Decimal = Decimal("450000"),
        total_liabilities: Decimal = Decimal("180000"),
        equity: Decimal = Decimal("270000"),
        ebit: Decimal = Decimal("38000"),
        interest: Decimal = Decimal("9500"),
    ) -> SolvencyReport:
        journal = self._journal_repo.get_journal()
        return self._ratio_engine.calculate(
            journal,
            current_assets=current_assets,
            current_liabilities=current_liabilities,
            total_assets=total_assets,
            total_liabilities=total_liabilities,
            equity=equity,
            ebit=ebit,
            interest_expense=interest,
        )

    # --- Export ---
    def export_to_bank(self, reference: str = "") -> BankPackage:
        entries = self._journal_repo.get_all_entries()
        if not entries:
            # Seed a couple of demo entries if empty
            self._seed_demo_entries()

        entries = self._journal_repo.get_all_entries()
        pkg = self._bank_exporter.export(entries, reference=reference)

        # Also record in fraud log as a sensitive action
        ctx = PolicyContext(amount=pkg.total_amount, has_digital_signature=True, source="export")
        self._fraud_policy.evaluate(ctx, "export_bank")
        return pkg

    def verify_export(self, pkg: BankPackage) -> bool:
        return self._bank_exporter.verify_package(pkg)

    # --- Fraud log access ---
    def get_fraud_attempts(self):
        return self._fraud_log.get_all()

    def get_blocked_attempts(self):
        return self._fraud_log.get_blocked()

    # Internal helpers
    def _seed_demo_entries(self):
        """Create a couple of realistic entries for first-time demo."""
        self.post_manual_entry(
            "Recebimento inicial de capital",
            "1.1.01",
            "3.1.01",
            Decimal("100000"),
        )
        self.post_manual_entry(
            "Pagamento fornecedor (NF-e 12345)",
            "2.1.01",
            "1.1.01",
            Decimal("18500"),
        )
