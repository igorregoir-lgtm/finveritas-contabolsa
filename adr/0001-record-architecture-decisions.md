# ADR 0001: Record Architecture Decisions

## Status

Accepted

## Context

FinVeritas Contabolsa is evolving from a prototype into a production-grade
accounting system. We need a lightweight, version-controlled record of the
significant architectural choices so that future contributors can understand
the rationale behind the structure and avoid revisiting settled debates.

## Decision

We will use Architecture Decision Records (ADRs) in the `adr/` directory.
Each record follows the Nygard format (status, context, decision,
consequences) and is numbered sequentially.

## Consequences

- **Positive**: Decisions are discoverable, auditable, and linked to git history.
- **Positive**: New contributors can read the decision log instead of relying on oral history.
- **Negative**: A small overhead is added when making significant architectural changes.
- **Negative**: ADRs can become stale if not updated when decisions change.

## Related

- This record follows Michael Nygard's ADR template.
- All subsequent ADRs in this directory reference this convention.
