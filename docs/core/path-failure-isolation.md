# Path failure isolation

`Orchestrator.run_cycle()` loops `PathConfig` entries independently.

## try/except per path

An exception during one path's graph invoke is logged, recorded if possible, and the loop **continues** to the next path.

## Test coverage

`tests/unit/test_orchestrator.py::test_run_cycle_continues_after_one_path_fails` asserts the second path still runs when the first raises.

## Rationale

Multi-hop monitoring should not halt entirely because a single pool id misconfigured or Drips rejected one adjustment.

See `core/orchestrator.py` `run_cycle`.
