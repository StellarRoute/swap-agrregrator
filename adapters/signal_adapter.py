# Provides external market-velocity + sentiment signals for tracked assets.
from __future__ import annotations

import random
import time
from abc import ABC, abstractmethod

from core.state import SignalSnapshot


class SignalProvider(ABC):
    @abstractmethod
    def get_signal(self, asset: str) -> SignalSnapshot:
        """Return the latest velocity/sentiment signal for `asset`."""


class MockSignalProvider(SignalProvider):
    """Deterministic synthetic signal generator, seeded per asset and time bucket.

    Real provider selection is pending PRD Open Question #2 (which sentiment/market-data
    API is licensed). This implements the full SignalProvider contract so the prediction
    agent can be built and tested against it now, and swapped for a real provider later
    without any agent code changes.
    """

    def __init__(self, stale_probability: float = 0.0, bucket_seconds: int = 30) -> None:
        self._stale_probability = stale_probability
        self._bucket_seconds = bucket_seconds

    def get_signal(self, asset: str) -> SignalSnapshot:
        bucket = int(time.time() // self._bucket_seconds)
        rng = random.Random(f"{asset}:{bucket}")
        stale = rng.random() < self._stale_probability
        return SignalSnapshot(
            asset=asset,
            velocity_score=rng.uniform(-1.0, 1.0),
            sentiment_score=rng.uniform(-1.0, 1.0),
            stale=stale,
        )


class HttpSignalProvider(SignalProvider):
    """Calls configured market-velocity and sentiment HTTP APIs.

    The concrete provider is unresolved (PRD Open Question #2); this assumes each API
    exposes `GET {base_url}/velocity?asset=<code>` -> {"velocity": float} and
    `GET {base_url}/sentiment?asset=<code>` -> {"sentiment": float}, both roughly -1..1.
    Update the parsing here once a real provider is selected — no other code changes,
    since callers depend only on the SignalProvider interface.
    """

    def __init__(
        self,
        market_data_base_url: str,
        market_data_api_key: str,
        sentiment_base_url: str,
        sentiment_api_key: str,
        timeout_seconds: float = 5.0,
    ) -> None:
        import httpx

        self._market_data_base_url = market_data_base_url.rstrip("/")
        self._sentiment_base_url = sentiment_base_url.rstrip("/")
        self._market_data_api_key = market_data_api_key
        self._sentiment_api_key = sentiment_api_key
        self._client = httpx.Client(timeout=timeout_seconds)

    def get_signal(self, asset: str) -> SignalSnapshot:
        import httpx

        try:
            velocity_resp = self._client.get(
                f"{self._market_data_base_url}/velocity",
                params={"asset": asset},
                headers={"Authorization": f"Bearer {self._market_data_api_key}"},
            )
            velocity_resp.raise_for_status()
            velocity = float(velocity_resp.json()["velocity"])

            sentiment_resp = self._client.get(
                f"{self._sentiment_base_url}/sentiment",
                params={"asset": asset},
                headers={"Authorization": f"Bearer {self._sentiment_api_key}"},
            )
            sentiment_resp.raise_for_status()
            sentiment = float(sentiment_resp.json()["sentiment"])

            return SignalSnapshot(
                asset=asset, velocity_score=velocity, sentiment_score=sentiment, stale=False
            )
        except (httpx.HTTPError, KeyError, ValueError, TypeError):
            # Upstream failure (F2 acceptance criterion): degrade to a stale, neutral signal
            # instead of raising, so a flaky external API can't crash the orchestration loop.
            return SignalSnapshot(asset=asset, velocity_score=0.0, sentiment_score=0.0, stale=True)
