# Soroban pool state adapter

`adapters/soroban_adapter.py` supplies pool reserve history for the orchestrator.

## FixturePoolStateProvider

Default for local dev and tests. Seeds a deterministic RNG per `pool_id` and synthesizes depleting reserves over `lookback` snapshots (30 second spacing).

## SorobanPoolStateProvider

Intended for testnet/mainnet reads via `SorobanServer`. Calls `get_reserves` on the pool contract. Today `_fetch_reserves` raises `NotImplementedError` until the StellarRoute contract ABI is confirmed.

Returns a single snapshot per poll; history must be accumulated across orchestrator cycles.

## Selection

`workers/tasks.py` `_build_pool_provider()` picks mock/fixture vs Soroban based on `Settings` (see `docs/workers/adapter-factory-wiring.md`).
