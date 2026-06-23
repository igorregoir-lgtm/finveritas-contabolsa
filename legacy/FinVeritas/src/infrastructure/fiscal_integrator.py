"""
Real FiscalIntegrator implementation.

Handles Pix + NF-e import, basic validation, signature guard, and reconciliation to Journal.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Tuple
import hashlib

from ..domain.models.fiscal import PixPayment, NFeDocument, ReconciledFiscalEntry
from ..domain.models.journal import JournalEntry, JournalLine, Account, AccountType, create_entry
from ..domain.guardrails.anti_fraud_policy import AntiFraudPolicy, PolicyContext, FraudDecision


class FiscalIntegrator:
    """
    Production-grade (demo) adapter for Pix + NF-e.

    Responsibilities:
    - Validate structure and business rules
    - Enforce digital signature via Guardrails
    - Reconcile Pix amount with NF-e (when present)
    - Produce reconciled entry and corresponding JournalEntry
    """

    def __init__(self, fraud_policy: AntiFraudPolicy):
        self._policy = fraud_policy

    def _validate_pix(self, pix: dict) -> PixPayment:
        # Minimal parsing + validation
        required = ["txid", "amount", "payer", "payee", "timestamp"]
        for field in required:
            if field not in pix:
                raise ValueError(f"Pix missing required field: {field}")

        return PixPayment(
            txid=pix["txid"],
            amount=Decimal(str(pix["amount"])),
            payer_cnpj_cpf=pix["payer"],
            payee_cnpj_cpf=pix["payee"],
            timestamp=datetime.fromisoformat(pix["timestamp"]) if isinstance(pix["timestamp"], str) else pix["timestamp"],
            description=pix.get("description", ""),
            has_digital_signature=bool(pix.get("has_digital_signature", False)),
            raw=pix,
        )

    def _validate_nfe(self, nfe: Optional[dict]) -> Optional[NFeDocument]:
        if not nfe:
            return None

        required = ["chave_acesso", "numero", "emitente", "destinatario", "valor_total", "data_emissao"]
        for field in required:
            if field not in nfe:
                raise ValueError(f"NF-e missing required field: {field}")

        return NFeDocument(
            chave_acesso=nfe["chave_acesso"],
            numero=nfe["numero"],
            emitente_cnpj=nfe["emitente"],
            destinatario_cnpj=nfe["destinatario"],
            valor_total=Decimal(str(nfe["valor_total"])),
            data_emissao=datetime.fromisoformat(nfe["data_emissao"]) if isinstance(nfe["data_emissao"], str) else nfe["data_emissao"],
            has_digital_signature=bool(nfe.get("has_digital_signature", False)),
            raw=nfe,
        )

    def importar_pix_nfe(
        self,
        pix_data: dict,
        nfe_data: Optional[dict] = None,
        actor: str = "system",
    ) -> Tuple[ReconciledFiscalEntry, Optional[JournalEntry]]:
        """
        Main entry point. Raises on validation or fraud block.
        Returns (reconciled, optional_journal_entry)
        """
        pix = self._validate_pix(pix_data)
        nfe = self._validate_nfe(nfe_data)

        # Build policy context
        ctx = PolicyContext(
            amount=pix.amount,
            has_digital_signature=pix.has_digital_signature and (nfe is None or nfe.has_digital_signature),
            source="fiscal_import",
            actor=actor,
        )

        decision = self._policy.evaluate(ctx, "import_fiscal")
        if self._policy.is_blocked(decision):
            raise PermissionError(f"Fraud policy blocked import: {pix.txid}")

        # Reconciliation logic
        reconciled_amount = pix.amount
        warnings = []

        if nfe:
            if pix.amount != nfe.valor_total:
                warnings.append(f"Pix amount {pix.amount} differs from NF-e total {nfe.valor_total}")
            # In real system we would do more cross-checks (CNPJ, dates, etc.)

        # Create reconciled record (id will be used as reference)
        reconciled = ReconciledFiscalEntry(
            id=f"rec_{pix.txid[:8]}",
            pix=pix,
            nfe=nfe,
            reconciled_amount=reconciled_amount,
            journal_entry_id="",  # filled after journal post
            validated_at=datetime.now(timezone.utc),
            warnings=warnings,
        )

        # Optionally produce a JournalEntry (typical flow)
        journal_entry = None
        if True:  # always produce for demo
            # Example accounts (hardcoded for demo)
            bank_or_cash = Account("1.1.01", "Caixa / Banco", AccountType.ASSET)
            revenue_or_receivable = Account("3.1.01", "Receita de Serviços", AccountType.REVENUE)

            lines = [
                JournalLine(account=bank_or_cash, debit=reconciled_amount, description=f"Pix {pix.txid}"),
                JournalLine(account=revenue_or_receivable, credit=reconciled_amount, description="Contrapartida"),
            ]

            journal_entry = create_entry(
                description=f"Importação Pix+NF-e {pix.txid}",
                lines=lines,
                source="fiscal_import",
                metadata={"reconciled_id": reconciled.id, "pix_txid": pix.txid},
            )
            reconciled = ReconciledFiscalEntry(  # rebuild with journal ref
                **{**reconciled.__dict__, "journal_entry_id": journal_entry.id}
            )

        return reconciled, journal_entry
