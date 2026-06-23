from harness.golden_consolidation import run_golden_harness


def test_golden_harness():
    """Runs the full golden consolidation harness as a pytest test."""
    assert run_golden_harness() is True
