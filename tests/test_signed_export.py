"""
Tests for the signed PDF/JSON export package.
"""

import os
from decimal import Decimal

import pytest

from src.domain.ratio_engine import RatioEngine, SolvencyCard
from src.infrastructure.signed_export import SignedExporter


@pytest.fixture
def sample_card() -> SolvencyCard:
    engine = RatioEngine()
    return engine.calculate(
        current_assets=Decimal("400000"),
        current_liabilities=Decimal("200000"),
        inventory=Decimal("50000"),
        cash=Decimal("100000"),
        total_assets=Decimal("1000000"),
        total_liabilities=Decimal("500000"),
        equity=Decimal("500000"),
        ebit=Decimal("200000"),
        ebitda=Decimal("250000"),
        interest_expense=Decimal("25000"),
        net_debt=Decimal("300000"),
        sales=Decimal("1000000"),
        retained_earnings=Decimal("100000"),
    )


class FakeEvent:
    def __init__(self, event_id: str, description: str):
        self.event_id = event_id
        self.description = description

    def to_dict(self) -> dict:
        return {"event_id": self.event_id, "description": self.description}


def test_generate_signed_package_creates_pdf_and_json(sample_card: SolvencyCard):
    exporter = SignedExporter()
    events = [FakeEvent("ev-1", "Entry A"), FakeEvent("ev-2", "Entry B")]

    pkg = exporter.generate_signed_package(events, sample_card, "Allla Group")

    assert pkg["verified"] is True
    assert pkg["format"] == "pdf+json"
    assert pkg["content_hash"]
    assert pkg["signature"].startswith("SIG-")
    assert pkg["pdf_path"]
    assert os.path.exists(pkg["pdf_path"])
    assert pkg["payload_preview"]["events"] == 2
    assert pkg["payload_preview"]["status"] == sample_card.overall_status

    os.remove(pkg["pdf_path"])


def test_generate_signed_package_empty_events(sample_card: SolvencyCard):
    exporter = SignedExporter()
    pkg = exporter.generate_signed_package([], sample_card, "EmptyCo")

    assert pkg["payload_preview"]["events"] == 0
    assert os.path.exists(pkg["pdf_path"])

    os.remove(pkg["pdf_path"])


def test_generate_signed_package_hash_is_verifiable(sample_card: SolvencyCard):
    exporter = SignedExporter()
    events = [FakeEvent("ev-1", "Entry A")]
    pkg = exporter.generate_signed_package(events, sample_card, "HashCo")

    assert len(pkg["content_hash"]) == 64
    assert pkg["signature"].startswith("SIG-")

    os.remove(pkg["pdf_path"])


def test_pdf_generation_directly(sample_card: SolvencyCard):
    exporter = SignedExporter()
    path = "test_direct.pdf"
    exporter._generate_pdf(path, "DirectCo", sample_card, 3, "HASH" * 16, "SIG-TEST")

    assert os.path.exists(path)
    assert os.path.getsize(path) > 0

    os.remove(path)


def test_generate_group_credit_memo(sample_card: SolvencyCard):
    exporter = SignedExporter()
    covenants = [
        {
            "code": "LEV-01",
            "observed_value": Decimal("2.56"),
            "threshold": Decimal("3.0"),
            "headroom": Decimal("0.44"),
            "status": "PASS",
        }
    ]
    consol_data = {
        "total_revenue_external": Decimal("1000000"),
        "ic_eliminated_loan": Decimal("5000000"),
        "ic_eliminated_arap": Decimal("7000000"),
    }
    path = exporter.generate_group_credit_memo(
        group_name="Allla Group",
        consol_data=consol_data,
        covenants=covenants,
        elims_count=2,
        root_hash="ROOT" * 16,
        explains_count=4,
    )

    assert os.path.exists(path)
    assert os.path.getsize(path) > 0

    os.remove(path)
