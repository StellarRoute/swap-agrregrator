# Environment variables

Loaded by `config/settings.py` (`Settings` class). See `.env.example` for template.

## Core

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `development` | Environment label |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

## Database

| Variable | Default |
|----------|---------|
| `DATABASE_URL` | `postgresql://stellarhydra:stellarhydra@localhost:5432/stellarhydra` |

## Redis / Celery

| Variable | Purpose |
|----------|---------|
| `REDIS_URL` | General Redis |
| `CELERY_BROKER_URL` | Task broker |
| `CELERY_RESULT_BACKEND` | Task results |

## Stellar

| Variable | Description |
|----------|-------------|
| `SOROBAN_RPC_URL` | Soroban RPC endpoint |
| `STELLAR_NETWORK_PASSPHRASE` | Network passphrase |
| `STELLARROUTE_CONTRACT_ID` | Pool reader contract (optional) |

## Drips

| Variable | Description |
|----------|-------------|
| `DRIPS_API_BASE_URL` | Drips API base |
| `DRIPS_API_KEY` | API key |
| `DRIPS_ACCOUNT_ID` | Account context |
| `USE_MOCK_DRIPS_CLIENT` | Use mock when `true` |

## Signals

| Variable | Description |
|----------|-------------|
| `SENTIMENT_API_*`, `MARKET_DATA_API_*` | External providers |
| `USE_MOCK_SIGNAL_PROVIDER` | Mock when `true` |

## Risk

| Variable | Default | Description |
|----------|---------|-------------|
| `RISK_SCORE_THRESHOLD` | `0.65` | Minimum score to act |
| `MAX_STREAM_DELTA_PER_CYCLE` | `1000` | Max drip delta |
| `MAX_PATH_CAPITAL_PCT` | `0.25` | Capital cap per path |
| `REBALANCE_COOLDOWN_SECONDS` | `300` | Cooldown between actions |
| `KILL_SWITCH_ENGAGED` | `false` | Startup kill switch state |

## Admin

| Variable | Description |
|----------|-------------|
| `ADMIN_API_KEY` | Required for protected admin routes |
| `EXECUTOR_FAILURE_ALERT_THRESHOLD` | Alert after N failures |
