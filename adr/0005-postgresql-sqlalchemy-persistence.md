# ADR 0005: PostgreSQL Persistence via SQLAlchemy

## Status

Accepted

## Context

The system must persist journal events durably. SQLite is insufficient for
concurrent production use, and NoSQL would complicate the relational queries
needed for balance reporting and covenant checks.

## Decision

We use PostgreSQL as the production database, accessed through SQLAlchemy ORM.
Events are stored as JSON records with explicit columns for the hash chain
fields (`previous_hash`, `current_hash`). The repository loads events, orders
them by timestamp, and re-verifies the hash chain before returning them to
the domain.

## Consequences

- **Positive**: Mature, transactional, and concurrent persistence.
- **Positive**: JSON column allows flexible event payloads while keeping critical fields indexed.
- **Positive**: SQLAlchemy enables type-checked queries and easy migration.
- **Negative**: Requires PostgreSQL in production; local development uses Docker Compose.
- **Negative**: Event payload shape is not enforced by the database schema; domain validation is required.

## Related

- `src/infrastructure/database.py`
- `src/infrastructure/event_repository.py`
- `docker-compose.yml`
