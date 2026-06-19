# Tracked paths configuration

Monitored swap paths are defined in code today, not loaded from a database.

## TRACKED_PATHS

`scripts/run_orchestrator.py` lists `PathConfig` entries:

| path_id | hops | pool_ids |
|---------|------|----------|
| XLM-USDC-yXLM | XLM → USDC → yXLM | two pools |
| XLM-AQUA | XLM → AQUA | one pool |

## PathConfig invariants

- `len(pool_ids) == len(hops) - 1`
- `path_id` is stable for metrics and checkpoint thread scoping

## Extending

Add another `PathConfig` to the list or refactor to YAML/env when dynamic path management ships.

See `core/state.py` for the dataclass definition.
