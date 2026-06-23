# CI entry-point — delegates to the canonical harness test
# Use: python -m pytest tests/ -q   (preferred)
# or:  python harness/ci/test_harness.py  (legacy CI scripts)
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from harness.golden_consolidation import run_golden_harness

if __name__ == "__main__":
    print("Running FinVeritas golden harness...")
    ok = run_golden_harness()
    if not ok:
        print("❌ Harness failed")
        sys.exit(1)
    print("✅ All checks passed")
