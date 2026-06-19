# LangGraph checkpointing

Phase 2 orchestrator accepts a pluggable `BaseCheckpointSaver`.

## Default checkpointer

`_default_checkpointer()` returns `PostgresSaver` when `DATABASE_URL` is configured and `langgraph-checkpoint-postgres` is installed.

## thread_id per path

Each `run_cycle` iteration uses:

```
thread_id = f"{path.path_id}-{uuid4()}"
```

Passed in `config={"configurable": {"thread_id": thread_id}}` so restarts can resume in-flight paths.

## Dependency

Listed in `pyproject.toml` as `langgraph-checkpoint-postgres`. Without it, orchestrator falls back to in-memory checkpointing.

See `core/orchestrator.py`.
