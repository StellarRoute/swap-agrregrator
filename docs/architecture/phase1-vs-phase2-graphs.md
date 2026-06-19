# Phase 1 vs Phase 2 graphs

Two LangGraph topologies coexist in the repo.

## Phase 1 (`core/graph.py`)

Synchronous in-process graph: ingest pool/signal, predict, decide, execute. Used for early demos and unit tests.

## Phase 2 (`core/orchestrator.py`)

Queue-backed graph (`_build_queued_graph`):

- Ingest nodes dispatch Celery tasks and block on `.get(timeout=...)`
- Adds `enforce_limits` node after `decide`
- Supports Postgres checkpointing per path `thread_id`
- `run_cycle` loops multiple `PathConfig` entries with failure isolation

Production orchestration should use Phase 2; Phase 1 remains for lightweight testing.
