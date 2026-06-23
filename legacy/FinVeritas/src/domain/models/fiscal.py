"""Fiscal domain models (Pix + NF-e) for Clara Contábil."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class PixPayment:
    txid: str
    amount: Decimal
    payer_cnpj_cpf: str
    payee_cnpj_cpf: str
    timestamp: datetime
    description: str = ""
    has_digital_signature: bool = False   # For demo: would come from e-signature / certificate
    raw: dict = None   # original payload if needed

    def __post_init__(self):
        if self.amount <= 0:
            raise ValueError("Pix amount must be positive")


@dataclass(frozen=True)
class NFeDocument:
    chave_acesso: str
    numero: str
    emitente_cnpj: str
    destinatario_cnpj: str
    valor_total: Decimal
    data_emissao: datetime
    has_digital_signature: bool = False
    items: list = None   # simplified
    raw: dict = None

    def __post_init__(self):
        if self.valor_total <= 0:
            raise ValueError("NF-e total must be positive")


@dataclass(frozen=True)
class ReconciledFiscalEntry:
    """Result of successful fiscal import + reconciliation."""
    id: str
    pix: PixPayment
    nfe: Optional[NFeDocument]
    reconciled_amount: Decimal
    journal_entry_id: str
    validated_at: datetime
    warnings: list = None
