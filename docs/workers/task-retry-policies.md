# Task retry policies

Celery tasks in `workers/tasks.py` use different retry settings.

## ingest_pool_task / ingest_signal_task

Retry on transient failures with bounded backoff (see task decorators for `max_retries` and `countdown`).

## execute_drips_adjustment_task

Higher retry tolerance because Drips API outages are expected; failures increment `executor_failures_total` and may trigger alerts after consecutive failures in the orchestrator.

## Orchestrator timeout

Ingest nodes use `.get(timeout=task_timeout)` where `task_timeout` is the max of poll interval settings (minimum 10 seconds). `CeleryTimeoutError` yields empty history or stale signals rather than crashing the graph.

See `core/orchestrator.py` ingest nodes.
