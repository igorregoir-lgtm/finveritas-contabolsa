"""
API contract tests for FinVeritas Contabolsa.
Covers health, journal entries, solvency, fiscal import, fraud log, and consolidation.
"""

from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "finveritas" in data["service"]


def test_journal_entry_and_solvency():
    entry = {
        "description": "Test double-entry",
        "lines": [
            {"account": "cash", "debit": 1000.0, "credit": 0.0, "description": "Receive cash"},
            {"account": "revenue", "debit": 0.0, "credit": 1000.0, "description": "Earn revenue"},
        ],
        "actor": "pytest",
    }
    r = client.post("/journal/entry", json=entry)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "id" in data
    assert "hash" in data
    assert len(data["hash"]) == 64  # SHA-256 hex

    solvency = client.get("/solvency")
    assert solvency.status_code == 200
    s = solvency.json()
    assert isinstance(s["credit_score"], int)
    assert s["overall_status"] in ("GREEN", "YELLOW", "RED")
    assert len(s["ratios"]) > 0


def test_fiscal_import():
    payload = {
        "pix": {
            "amount": 500.0,
            "counterparty": "Supplier A",
            "description": "Payment",
        },
        "nfe": None,
        "actor": "pytest",
    }
    r = client.post("/fiscal/import", json=payload)
    assert r.status_code == 200, r.text


def test_fraud_log():
    # Trigger a high-value action to generate a fraud log entry
    client.post(
        "/fiscal/import",
        json={
            "pix": {"amount": 200000.0, "counterparty": "X", "description": "Big"},
            "nfe": None,
            "actor": "pytest",
        },
    )
    r = client.get("/fraud-log")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert all(k in data[0] for k in ("timestamp", "action", "decision", "reason"))


def test_consolidation_flow():
    r = client.post("/consolidation/load-group")
    assert r.status_code == 200, r.text

    r = client.post("/consolidation/run")
    assert r.status_code == 200, r.text
    consol = r.json()
    assert "elims" in consol
    assert "matches" in consol
    assert "explains" in consol

    r = client.get("/consolidation/covenants")
    assert r.status_code == 200
    covenants = r.json()
    assert isinstance(covenants, list)
    if covenants:
        assert all(k in covenants[0] for k in ("covenant_code", "observed_value", "threshold", "status", "headroom"))


def test_what_if():
    client.post("/consolidation/load-group")
    r = client.post("/consolidation/what-if", json={"interco_loan_delta_m": 1.0, "ebitda_multiplier": 1.1})
    assert r.status_code == 200, r.text


def test_export_to_bank():
    r = client.post("/export")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["verified"] is True
    assert data["format"] == "pdf+json"
    assert data["pdf_path"]


def test_stress_test():
    client.post("/consolidation/load-group")
    r = client.post("/consolidation/stress", json={"stress_factor": 0.2})
    assert r.status_code == 200, r.text
    data = r.json()
    assert "stressed_covenants" in data
    assert "stressed_metrics" in data


def test_covenant_trends():
    r = client.get("/consolidation/trends")
    assert r.status_code == 200, r.text
    assert isinstance(r.json(), list)


def test_anomaly_detection():
    r = client.get("/consolidation/anomalies")
    assert r.status_code == 200, r.text
    assert isinstance(r.json(), list)


def test_export_bank_pack():
    client.post("/consolidation/load-group")
    r = client.post("/consolidation/export-bank-pack")
    assert r.status_code == 200, r.text
    data = r.json()
    assert "covenants" in data
    assert "elims_count" in data
    assert "explain_count" in data
