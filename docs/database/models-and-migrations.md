# Database models and migrations

## ORM

`db/models.py` - SQLAlchemy models for audit and orchestration state.

## Sessions

`db/session.py` - `SessionFactory` context manager used by admin API and workers.

## Migrations

Alembic config: `alembic.ini`

Initial revision: `db/migrations/versions/0001_initial.py`

## Apply migrations

```bash
alembic upgrade head
```

Required before Phase 2 orchestrator or admin audit log queries.

## Production

Run migrations against target `DATABASE_URL` before rolling out new images (see `deploy/README.md`).

## Admin queries

`core/observability.py` function `query_audit_log()` powers `GET /audit-log` with optional filters.
