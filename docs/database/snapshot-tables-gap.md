# Snapshot tables gap

Alembic migration `0001_initial` creates `pool_snapshots` and `signal_snapshots` tables mapped by `PoolSnapshotRecord` and `SignalSnapshotRecord` in `db/models.py`.

## Runtime behavior

No ingestion task or orchestrator node writes to these tables today. History lives in-memory inside `GraphState` for the duration of a cycle.

## Implication

Operators should not query snapshot tables for analytics until a persistence job is implemented. Use `agent_run_log` for audit entries instead.

See `docs/database/models-and-migrations.md` for tables that are actively written.
