# Typed, fail-fast environment configuration loaded once and shared across the app.
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = "development"
    log_level: str = "INFO"

    database_url: str = "postgresql://stellarhydra:stellarhydra@localhost:5432/stellarhydra"

    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    soroban_rpc_url: str = "https://soroban-testnet.stellar.org"
    stellar_network_passphrase: str = "Test SDF Network ; September 2015"
    stellarroute_contract_id: str | None = None

    drips_api_base_url: str = "https://api.drips.network"
    drips_api_key: str | None = None
    drips_account_id: str | None = None
    use_mock_drips_client: bool = True

    sentiment_api_base_url: str | None = None
    sentiment_api_key: str | None = None
    market_data_api_base_url: str | None = None
    market_data_api_key: str | None = None
    use_mock_signal_provider: bool = True

    risk_score_threshold: float = 0.65
    max_stream_delta_per_cycle: float = 1000.0
    max_path_capital_pct: float = 0.25
    rebalance_cooldown_seconds: int = 300
    kill_switch_engaged: bool = False

    tracked_paths: str = "xlm-usdc,yxlm-xlm"

    pool_poll_interval_seconds: int = 30
    signal_poll_interval_seconds: int = 30

    admin_api_key: str | None = None
    executor_failure_alert_threshold: int = 3


@lru_cache
def get_settings() -> Settings:
    return Settings()


def tracked_path_ids(settings: Settings | None = None) -> list[str]:
    cfg = settings or get_settings()
    return [item.strip() for item in cfg.tracked_paths.split(",") if item.strip()]
