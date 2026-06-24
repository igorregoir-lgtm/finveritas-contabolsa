# 0007. CI pip dependency caching

## Status

Accepted

## Context

The CI pipeline installs Python dependencies on every run. As the quality gate
expands to include ruff, mypy, bandit, pip-audit, detect-secrets, pytest-cov,
nox, and the full requirements.txt, the "Install dependencies" step became a
significant and repeated source of CI minutes. This is wasteful for a
high-frequency PDCA workflow where many commits are small style or test
adjustments.

## Decision

Use the built-in `cache: 'pip'` option of `actions/setup-python@v5` in the
Python-based CI jobs (`backend` and `mutation`). Set `cache-dependency-path` to
`requirements.txt` and `pyproject.toml` so the cache key invalidates when
dependencies or build metadata change.

## Consequences

- Faster CI feedback loops and lower compute usage.
- Cache invalidation is automatic when dependency files change.
- The cache does not cover Nox-created virtualenvs; that remains a future
  optimization if CI times continue to grow.
