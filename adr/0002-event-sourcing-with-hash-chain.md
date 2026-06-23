# ADR 0002: Event Sourcing with SHA-256 Hash Chain

## Status

Accepted

## Context

The system must store financial journal entries in a way that is tamper-evident
and auditable. Traditional relational journaling can be silently modified, which
is unacceptable for financial records that may be inspected by auditors, banks,
and regulators.

## Decision

We will use event sourcing with immutable `AccountingEvent` records. Each event
contains a `previous_hash` and a self-computed `current_hash` using SHA-256 over
a canonical JSON representation. The journal verifies the chain on load, and
the SQLAlchemy repository re-verifies the chain when loading from PostgreSQL.

## Consequences

- **Positive**: Any tampering with a stored event breaks the chain and is detected immediately.
- **Positive**: The full history is preserved, enabling audit trails and point-in-time reconstruction.
- **Positive**: Hash verification is deterministic and fast enough for startup checks.
- **Negative**: Storage grows monotonically; there is no destructive update or deletion of events.
- **Negative**: Correctness of the hash computation must be tested rigorously; a bug in hashing would break the chain.

## Related

- `src/domain/journal.py`
- `src/infrastructure/event_repository.py`
- `tests/test_event_repository.py`
