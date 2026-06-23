# ADR 0006: Nox Cross-Platform Quality Gate

## Status

Accepted

## Context

The project must be developed on Windows, Linux, and macOS. The CI pipeline
runs on Ubuntu, but local developers may run Windows. We need a single
command that reproduces the CI gate on any operating system.

## Decision

We use `nox` to define sessions for lint, typecheck, security, tests, and
frontend build. The default `nox` run executes the full gate, while `nox -s ci`
runs the backend-only gate for developers without Node. The CI workflow calls
the same `nox -s ci` session, ensuring local and remote checks are identical.

## Consequences

- **Positive**: Local developers can reproduce CI exactly.
- **Positive**: Session isolation prevents environment drift.
- **Positive**: Adding a new check (e.g., detect-secrets) only requires editing `noxfile.py`.
- **Negative**: Running nox creates virtual environments, which adds time and disk usage.
- **Negative**: Some tools (e.g., mutmut) do not run natively on Windows; they are delegated to CI on Ubuntu.

## Related

- `noxfile.py`
- `.github/workflows/ci.yml`
- `CONTRIBUTING.md`
