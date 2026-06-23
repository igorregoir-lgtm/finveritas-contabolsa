# ADR 0004: FastAPI + React Layered Architecture

## Status

Accepted

## Context

The system needs a web API for programmatic access and a user-facing interface
for analysts. The backend must be type-safe, high-performance, and easy to
test. The frontend must be maintainable and offer a modern developer experience.

## Decision

We use a layered architecture:

- **Domain** (`src/domain/`): pure business logic, no external dependencies.
- **Application** (`src/application/`): service orchestration and use cases.
- **Infrastructure** (`src/infrastructure/`): persistence, PDF export, fiscal simulation.
- **API** (`src/api/`): FastAPI HTTP layer.
- **Frontend** (`frontend/`): React + Vite + TypeScript in strict mode.

The API depends on the application service, which depends on domain objects.
Infrastructure is injected via interfaces (`EventRepository`), keeping the domain
clean.

## Consequences

- **Positive**: Clear separation of concerns; business rules are isolated from frameworks.
- **Positive**: The backend can be tested without the frontend or a real database.
- **Positive**: FastAPI provides automatic OpenAPI documentation and strong typing.
- **Negative**: More directories and boilerplate than a simple MVC app.
- **Negative**: Developers must respect dependency direction to avoid circular imports.

## Related

- `src/api/main.py`
- `src/application/finveritas_service.py`
- `frontend/`
