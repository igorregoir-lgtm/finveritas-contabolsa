"""
Property-based API contract tests using Hypothesis.

These tests generate random inputs for the main API endpoints and verify that
the API never crashes with a 5xx status and returns a valid response.
"""

import os

# Force an in-memory SQLite database so the API lifespan initializes without
# requiring a real PostgreSQL server during property-based testing.
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

# Reset any cached settings instance so the env var above is respected.
from src.infrastructure import settings as settings_module

settings_module._settings = None

from fastapi.testclient import TestClient  # noqa: E402
from hypothesis import given  # noqa: E402
from hypothesis import settings as hypothesis_settings
from hypothesis import strategies as st

from src.api.main import app  # noqa: E402

client = TestClient(app)

VALID_STATUSES = {200, 201, 400, 403, 422}


def _amount_strategy():
    return st.one_of(st.just(0), st.floats(min_value=0, max_value=1e6, allow_nan=False, allow_infinity=False))


@hypothesis_settings(max_examples=20, deadline=None)
@given(
    lines=st.lists(
        st.fixed_dictionaries(
            {
                "account": st.text(min_size=1, max_size=20),
                "debit": _amount_strategy(),
                "credit": _amount_strategy(),
                "description": st.text(max_size=30),
            }
        ),
        min_size=1,
        max_size=5,
    )
)
def test_post_journal_entry_does_not_crash(lines):
    response = client.post(
        "/journal/entry",
        json={"description": "property-based test", "lines": lines},
    )
    assert response.status_code in VALID_STATUSES


@hypothesis_settings(max_examples=20, deadline=None)
@given(
    pix=st.fixed_dictionaries(
        {
            "chave": st.text(min_size=1, max_size=30),
            "valor": st.floats(min_value=0, max_value=1e6, allow_nan=False, allow_infinity=False),
        }
    )
    | st.dictionaries(st.text(min_size=1), st.text(min_size=1))
)
def test_post_fiscal_import_does_not_crash(pix):
    response = client.post(
        "/fiscal/import",
        json={"pix": pix},
    )
    assert response.status_code in VALID_STATUSES


@hypothesis_settings(max_examples=20, deadline=None)
@given(
    stress_factor=st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False)
)
def test_post_stress_does_not_crash(stress_factor):
    response = client.post("/consolidation/stress", json={"stress_factor": stress_factor})
    assert response.status_code in VALID_STATUSES


@hypothesis_settings(max_examples=20, deadline=None)
@given(
    interco=st.floats(min_value=-1e3, max_value=1e3, allow_nan=False, allow_infinity=False),
    multiplier=st.floats(min_value=0.0001, max_value=10, allow_nan=False, allow_infinity=False),
)
def test_post_what_if_does_not_crash(interco, multiplier):
    response = client.post(
        "/consolidation/what-if",
        json={"interco_loan_delta_m": interco, "ebitda_multiplier": multiplier},
    )
    assert response.status_code in VALID_STATUSES
