# Executes liquidity rebalancing by adjusting a Drips continuous funding stream.
from __future__ import annotations

import logging
from abc import ABC, abstractmethod

from core.state import ExecutionResult

logger = logging.getLogger(__name__)


class DripsClient(ABC):
    @abstractmethod
    def adjust_stream(self, target_pool_id: str, delta_amount: float) -> ExecutionResult:
        """Adjust the funding stream toward `target_pool_id` by `delta_amount`."""


class MockDripsClient(DripsClient):
    """Logs the intended stream adjustment instead of calling the Drips API.

    Used until the Drips Wave testnet/sandbox integration shape is confirmed
    (PRD Open Question #1). Implements the real DripsClient interface so the
    real client (built in Phase 3) is a drop-in replacement.
    """

    def adjust_stream(self, target_pool_id: str, delta_amount: float) -> ExecutionResult:
        logger.info(
            "MockDripsClient: would adjust stream toward pool=%s by delta=%s",
            target_pool_id,
            delta_amount,
        )
        return ExecutionResult(
            success=True,
            detail=f"mock: stream toward {target_pool_id} adjusted by {delta_amount:+.2f}",
        )


class HttpDripsClient(DripsClient):
    """Adjusts a Drips continuous funding stream via the Drips Wave HTTP API.

    The exact Drips Wave endpoint contract is unresolved (PRD Open Question #1); this
    assumes `POST {base_url}/accounts/{account_id}/streams/adjust` with JSON body
    `{"target": <pool id>, "delta": <amount>}`, bearer-authenticated. Update the request
    shape here once real sandbox access confirms the contract — no other code changes,
    since callers depend only on the DripsClient interface.
    """

    def __init__(
        self, base_url: str, api_key: str, account_id: str, timeout_seconds: float = 10.0
    ) -> None:
        import httpx

        self._base_url = base_url.rstrip("/")
        self._account_id = account_id
        self._client = httpx.Client(
            timeout=timeout_seconds, headers={"Authorization": f"Bearer {api_key}"}
        )

    def adjust_stream(self, target_pool_id: str, delta_amount: float) -> ExecutionResult:
        import httpx

        url = f"{self._base_url}/accounts/{self._account_id}/streams/adjust"
        try:
            response = self._client.post(url, json={"target": target_pool_id, "delta": delta_amount})
            response.raise_for_status()
            return ExecutionResult(
                success=True,
                detail=f"drips: stream toward {target_pool_id} adjusted by {delta_amount:+.2f}",
            )
        except httpx.HTTPError as exc:
            # Surfaced to the caller (workers/tasks.py), which retries with backoff (F5).
            return ExecutionResult(success=False, detail=f"drips API call failed: {exc}")
