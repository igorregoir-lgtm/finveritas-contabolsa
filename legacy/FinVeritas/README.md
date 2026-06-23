# Legacy FinVeritas prototype

This directory preserves the earlier FinVeritas prototype for reference. The consolidated, Tesla-level production artifact lives in the root of `Artefato`.

## What was kept

- `app.py` — original Streamlit demo with basic modules.
- `src/` — early domain/infrastructure code (anti-fraud, journal, ratios).
- `tests/` — first guardrail and journal tests.
- `demo-finveritas.html` — standalone HTML demo.
- `start-finveritas.ps1` — PowerShell launcher.

## Why it was superseded

The root artifact (`finveritas-contabolsa`) includes:

- Clean architecture (domain / application / infrastructure / API layers).
- Full event sourcing with SHA-256 hash chain verification.
- Intercompany consolidation engine with matching, elimination, and covenants.
- 92% test coverage with property-based and API contract tests.
- `nox`-based cross-platform quality gate (lint, typecheck, security, tests, frontend build).
- GitHub Actions CI with bandit, pip-audit, and npm audit.
- Docker Compose infrastructure, pre-commit hooks, EditorConfig, and CONTRIBUTING guide.

Keep this legacy folder only for historical comparison; do not run it in production.
