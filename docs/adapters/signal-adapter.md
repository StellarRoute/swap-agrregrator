# Signal adapter

File: `adapters/signal_adapter.py`

## Interface

`SignalProvider.get_signal(asset) -> SignalSnapshot`

Signals keyed by destination asset on each hop (assets demand flows into).

## Implementations

| Class | When used |
|-------|-----------|
| Mock provider | `USE_MOCK_SIGNAL_PROVIDER=true` (default) |
| `HttpSignalProvider` | External sentiment/market APIs |

## Configuration

| Variable | Purpose |
|----------|---------|
| `SENTIMENT_API_BASE_URL` / `_KEY` | Sentiment source |
| `MARKET_DATA_API_BASE_URL` / `_KEY` | Market data source |
| `USE_MOCK_SIGNAL_PROVIDER` | Toggle mock |

## Open question

PRD open question #2: select concrete provider before disabling mock in production.
