# Celery tasks decoupling slow external calls (RPC, signal APIs, Drips) from the
# orchestration loop's tick (PRD F10), with retry/backoff for upstream failures (F5).
from __future__ import annotations

import logging

from adapters.drips_adapter import DripsClient, HttpDripsClient, MockDripsClient
from adapters.signal_adapter import HttpSignalProvider, MockSignalProvider, SignalProvider
from adapters.soroban_adapter import (
    FixturePoolStateProvider,
    PoolStateProvider,
    SorobanPoolStateProvider,
)
from config.settings import get_settings
from db.persist import persist_pool_snapshot, persist_signal_snapshot
from db.session import session_scope
from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def _build_pool_provider() -> PoolStateProvider:
    settings = get_settings()
    if settings.stellarroute_contract_id:
        return SorobanPoolStateProvider(settings.soroban_rpc_url, settings.stellar_network_passphrase)
    return FixturePoolStateProvider()


def _build_signal_provider() -> SignalProvider:
    settings = get_settings()
    if settings.use_mock_signal_provider:
        return MockSignalProvider()
    if not settings.market_data_api_base_url:
        raise RuntimeError("MARKET_DATA_API_BASE_URL required when USE_MOCK_SIGNAL_PROVIDER=false")
    return HttpSignalProvider(
        market_data_base_url=settings.market_data_api_base_url,
        market_data_api_key=settings.market_data_api_key,
        sentiment_base_url=settings.sentiment_api_base_url,
        sentiment_api_key=settings.sentiment_api_key,
    )


def _build_drips_client() -> DripsClient:
    settings = get_settings()
    if settings.use_mock_drips_client:
        return MockDripsClient()
    if not settings.drips_api_base_url or not settings.drips_account_id:
        raise RuntimeError("DRIPS_API_BASE_URL and DRIPS_ACCOUNT_ID required when USE_MOCK_DRIPS_CLIENT=false")
    return HttpDripsClient(
        base_url=settings.drips_api_base_url,
        api_key=settings.drips_api_key,
        account_id=settings.drips_account_id,
    )


@celery_app.task(name="stellarhydra.ingest_pool", bind=True, max_retries=3, default_retry_delay=5)
def ingest_pool_task(self, pool_id: str, lookback: int = 10) -> list[dict]:
    try:
        provider = _build_pool_provider()
        snapshots = provider.get_pool_history(pool_id, lookback)
        with session_scope() as session:
            for snapshot in snapshots:
                persist_pool_snapshot(session, snapshot)
        return [s.model_dump() for s in snapshots]
    except Exception as exc:
        logger.warning("ingest_pool_task failed for pool_id=%s: %s", pool_id, exc)
        raise self.retry(exc=exc) from exc


@celery_app.task(name="stellarhydra.ingest_signal", bind=True, max_retries=3, default_retry_delay=5)
def ingest_signal_task(self, asset: str) -> dict:
    try:
        provider = _build_signal_provider()
        signal = provider.get_signal(asset)
        with session_scope() as session:
            persist_signal_snapshot(session, signal)
        return signal.model_dump()
    except Exception as exc:
        logger.warning("ingest_signal_task failed for asset=%s: %s", asset, exc)
        raise self.retry(exc=exc) from exc


@celery_app.task(
    name="stellarhydra.execute_drips_adjustment",
    bind=True,
    max_retries=5,
    default_retry_delay=10,
    retry_backoff=True,
    retry_backoff_max=120,
)
def execute_drips_adjustment_task(self, target_pool_id: str, delta_amount: float) -> dict:
    try:
        client = _build_drips_client()
        result = client.adjust_stream(target_pool_id, delta_amount)
        if not result.success:
            raise RuntimeError(result.detail)
        return result.model_dump()
    except Exception as exc:
        logger.warning("execute_drips_adjustment_task failed for pool=%s: %s", target_pool_id, exc)
        raise self.retry(exc=exc) from exc
