# Celery eager test harness

Orchestrator unit and chaos tests run Celery tasks inline without a broker.

## Fixture pattern

`tests/unit/test_orchestrator.py` defines `_eager_celery`:

```python
celery_app.conf.task_always_eager = True
celery_app.conf.task_eager_propagates = True
```

## Usage

Apply the fixture (or mirror settings in test setup) before invoking `Orchestrator.run_cycle()` so `task.delay().get()` executes synchronously in-process.

`test_chaos_degradation.py` uses the same pattern to simulate timeouts and failures deterministically.

Reset eager mode after tests if sharing a global `celery_app` instance.

See `workers/celery_app.py`.
