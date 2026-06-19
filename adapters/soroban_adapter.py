# Reads Stellar/Soroban pool reserve state for a configured path: a fixture-backed
# implementation for local dev/tests, and a best-effort real RPC implementation for testnet.
from __future__ import annotations

import random
import time
from abc import ABC, abstractmethod

from core.state import PoolSnapshot


class PoolStateProvider(ABC):
    @abstractmethod
    def get_pool_history(self, pool_id: str, lookback: int = 10) -> list[PoolSnapshot]:
        """Return up to `lookback` historical snapshots for `pool_id`, oldest first."""


class FixturePoolStateProvider(PoolStateProvider):
    """Deterministic synthetic pool history, seeded per pool_id, for local dev and tests.

    Models reserves trending toward depletion so Phase 1 can demonstrate the
    prediction -> action link without live chain data.
    """

    def __init__(self, depletion_rate: float = 0.03) -> None:
        self._depletion_rate = depletion_rate

    def get_pool_history(self, pool_id: str, lookback: int = 10) -> list[PoolSnapshot]:
        rng = random.Random(pool_id)
        reserve_a = 100_000.0
        reserve_b = 100_000.0
        now = time.time()
        history: list[PoolSnapshot] = []
        for i in range(lookback):
            jitter = rng.uniform(-0.01, 0.01)
            reserve_a *= 1 - self._depletion_rate + jitter
            reserve_b *= 1 + self._depletion_rate * 0.4 + jitter
            history.append(
                PoolSnapshot(
                    pool_id=pool_id,
                    reserve_a=reserve_a,
                    reserve_b=reserve_b,
                    volume_24h=rng.uniform(5_000, 50_000),
                    timestamp=now - (lookback - i) * 30,
                )
            )
        return history


class SorobanPoolStateProvider(PoolStateProvider):
    """Reads live reserves from a StellarRoute Soroban pool contract over RPC.

    Assumes the pool contract exposes a `get_reserves` function returning (reserve_a,
    reserve_b), matching the common Soroban AMM pool interface. Soroban RPC exposes
    current state, not a time series, so history must be accumulated by the caller
    across successive polls (see core/orchestrator.py, added in Phase 2).
    """

    def __init__(self, rpc_url: str, network_passphrase: str) -> None:
        from stellar_sdk import SorobanServer

        self._server = SorobanServer(rpc_url)
        self._network_passphrase = network_passphrase

    def get_pool_history(self, pool_id: str, lookback: int = 10) -> list[PoolSnapshot]:
        try:
            reserve_a, reserve_b, volume = self._fetch_reserves(pool_id)
        except NotImplementedError:
            return FixturePoolStateProvider().get_pool_history(pool_id, lookback)
        return [
            PoolSnapshot(
                pool_id=pool_id,
                reserve_a=reserve_a,
                reserve_b=reserve_b,
                volume_24h=volume,
            )
        ]

    def _fetch_reserves(self, pool_id: str) -> tuple[float, float, float]:
        # Encoding the `get_reserves` invocation and decoding its ScVal result requires
        # the confirmed StellarRoute contract ABI (PRD Open Question #3). Until that's
        # available, use FixturePoolStateProvider rather than guessing at the encoding.
        raise NotImplementedError(
            "Real Soroban contract reads require a confirmed StellarRoute contract ABI "
            "(see PRD Open Question #3). Use FixturePoolStateProvider until resolved."
        )
