"""
Simulated Pix + NF-e Integrator with guardrail enforcement
"""

from decimal import Decimal
from typing import Optional

from ..domain.anti_fraud_policy import AntiFraudPolicy
from ..domain.journal import Journal, JournalLine


class FiscalSimulator:
    def __init__(self, policy: AntiFraudPolicy, journal: Journal):
        self.policy = policy
        self.journal = journal

    def import_pix_nfe(self, pix: dict, nfe: Optional[dict] = None, actor: str = "user"):
        amount = Decimal(str(pix.get("amount", 0)))
        has_sig = bool(pix.get("has_digital_signature", False)) and (
            nfe is None or nfe.get("has_digital_signature", False)
        )

        chain_ok = self.journal.verify_integrity()

        decision = self.policy.evaluate("import_fiscal", amount, has_sig, chain_ok, velocity_high=False, actor=actor)
        if self.policy.is_blocked(decision):
            raise PermissionError(f"Anti-fraud blocked import: {decision.value}")

        # Create journal entry
        lines = [
            JournalLine("1.1.01 - Caixa/Bancos (Pix)", debit=amount, description=f"Pix {pix.get('txid')}"),
            JournalLine("3.1.01 - Receita de Serviços", credit=amount),
        ]
        event = self.journal.post_entry(f"Recebimento Pix + NF-e {pix.get('txid', '')}", lines, source="fiscal_import")
        return {"reconciled": True, "amount": amount, "journal_event_id": event.id}
