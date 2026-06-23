"""Bank export package generator with content hash and simulated digital signature."""

import hashlib
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Dict, Any
from dataclasses import dataclass, asdict

from ..domain.models.journal import JournalEntry


@dataclass
class BankPackage:
    id: str
    generated_at: datetime
    total_amount: Decimal
    entry_count: int
    manifest: Dict[str, Any]
    content_hash: str
    signature: str   # simulated
    metadata: Dict[str, Any]


class BankExporter:
    """
    Produces an auditable export package for banks.

    In production this would:
    - Generate real PDF or CNAB/OFX
    - Use real certificate for signature
    - Write to secure storage
    """

    def __init__(self, private_key: str = "DEMO_PRIVATE_KEY_FINVERITAS"):
        self._private_key = private_key

    def _compute_hash(self, data: str) -> str:
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    def _simulate_signature(self, content_hash: str) -> str:
        # In real life: sign with private key
        raw = (content_hash + self._private_key).encode()
        return "SIG_" + hashlib.sha256(raw).hexdigest()[:32].upper()

    def export(
        self,
        entries: List[JournalEntry],
        destination_bank: str = "B3-DEMO-BANK",
        reference: str = "",
    ) -> BankPackage:
        if not entries:
            raise ValueError("Cannot export empty set of entries")

        total = sum(e.total for e in entries)

        manifest = {
            "reference": reference or f"EXP-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M')}",
            "destination": destination_bank,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "entries": [
                {
                    "id": e.id,
                    "timestamp": e.timestamp.isoformat(),
                    "description": e.description,
                    "total": str(e.total),
                    "lines": [
                        {
                            "account": l.account.code,
                            "debit": str(l.debit),
                            "credit": str(l.credit),
                        }
                        for l in e.lines
                    ],
                }
                for e in entries
            ],
        }

        manifest_str = str(manifest)
        content_hash = self._compute_hash(manifest_str)
        signature = self._simulate_signature(content_hash)

        pkg = BankPackage(
            id=f"bankpkg_{content_hash[:12]}",
            generated_at=datetime.now(timezone.utc),
            total_amount=total,
            entry_count=len(entries),
            manifest=manifest,
            content_hash=content_hash,
            signature=signature,
            metadata={"destination_bank": destination_bank},
        )
        return pkg

    def verify_package(self, pkg: BankPackage) -> bool:
        """Self-contained verification for demo."""
        manifest_str = str(pkg.manifest)
        expected_hash = self._compute_hash(manifest_str)
        if expected_hash != pkg.content_hash:
            return False
        expected_sig = self._simulate_signature(pkg.content_hash)
        return expected_sig == pkg.signature
