# Contributing to FinVeritas Contabolsa

Thank you for helping push this project to Tesla-level excellence. Every contribution must pass the same quality gate that runs in CI.

## Local development setup

```powershell
python -m pip install -r requirements.txt
```

For the frontend:

```powershell
cd frontend
npm install
```

## Quality gate

Before opening a PR, run the cross-platform gate:

```powershell
python -m nox
```

This executes, in isolated virtual environments:

1. `ruff check src/ app.py tests/`
2. `mypy src/`
3. `bandit -r src/ -ll -ii` + `pip-audit --requirement requirements.txt`
4. `pytest tests/ --cov=src --cov-fail-under=90`
5. `cd frontend && npx tsc --noEmit && npm run build`

If you do not have Node, you can run the backend-only gate:

```powershell
python -m nox -s ci
```

## Commit style

We use conventional commits:

- `feat:` new feature
- `fix:` bug fix
- `ref:` refactor
- `test:` tests only
- `chore:` tooling / dependencies
- `docs:` documentation
- `ci:` CI/CD changes
- `security:` security hardening

Include `Co-Authored-By: Claude <noreply@anthropic.com>` when pair-programming with Claude.

## Architecture principles

- **Domain first**: business rules live in `src/domain/` and have no infrastructure dependencies.
- **Immutable hash chain**: every journal event must keep the chain verifiable.
- **Anti-fraud by default**: sensitive operations go through `AntiFraudPolicy`.
- **Type safety**: all public functions must be typed; `mypy` must pass.
- **Test coverage**: new domain logic must include tests; aim for >90% coverage.

## Pull request checklist

- [ ] `python -m nox -s ci` passes locally
- [ ] New code is covered by tests
- [ ] No `bandit` or `pip-audit` findings introduced
- [ ] README updated if user-facing behavior changed
- [ ] Commit message follows conventional commit format
