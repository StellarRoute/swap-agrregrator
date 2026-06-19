# Worker adapter factory wiring

`workers/tasks.py` builds providers at task runtime from `Settings`.

## Pool provider

| Condition | Provider |
|-----------|----------|
| `stellarroute_contract_id` set | `SorobanPoolStateProvider` |
| otherwise | `FixturePoolStateProvider` |

## Signal provider

| Condition | Provider |
|-----------|----------|
| `use_mock_signal_provider` true | `MockSignalProvider` |
| otherwise | `HttpSignalProvider` with market/sentiment URLs |

## Drips client

| Condition | Client |
|-----------|--------|
| `use_mock_drips_client` true | `MockDripsClient` |
| otherwise | `HttpDripsClient` |

Factories run per task invocation so env changes after worker boot require a worker restart.

See `config/settings.py` for flag definitions.
