# JSON structured logging

`configure_logging()` in `core/observability.py` installs `_JsonFormatter` on the root handler.

## Log line shape

```json
{
  "ts": 1710000000.0,
  "level": "INFO",
  "logger": "stellarhydra.orchestrator",
  "message": "..."
}
```

Exceptions add `exc_info` string when present.

## Usage

Call `configure_logging()` once at process entry (`run_orchestrator`, API main). Use `get_logger(__name__)` in modules.

Log aggregation stacks (Loki, CloudWatch) can parse one JSON object per line without regex.

See `core/observability.py`.
