# End-to-end Phase 1 cycle test: proves the prediction -> decision -> execution wiring,
# and that swapping in a fake adapter changes the outcome without touching agent code.
import uuid

from adapters.drips_adapter import DripsClient, MockDripsClient
from adapters.signal_adapter import SignalProvider
from adapters.soroban_adapter import FixturePoolStateProvider, PoolStateProvider
from config.settings import Settings
from core.graph import build_graph
from core.state import ExecutionResult, PathConfig, PoolSnapshot, SignalSnapshot


class _FlatPoolStateProvider(PoolStateProvider):
    """Fake adapter: reserves never move, so no bottleneck should ever be predicted."""

    def get_pool_history(self, pool_id: str, lookback: int = 10):
        return [
            PoolSnapshot(pool_id=pool_id, reserve_a=100_000, reserve_b=100_000, volume_24h=1_000)
            for _ in range(lookback)
        ]


class _FlatSignalProvider(SignalProvider):
    def get_signal(self, asset: str) -> SignalSnapshot:
        return SignalSnapshot(asset=asset, velocity_score=0.0, sentiment_score=0.0, stale=False)


class _RecordingDripsClient(DripsClient):
    def __init__(self) -> None:
        self.calls = []

    def adjust_stream(self, target_pool_id: str, delta_amount: float) -> ExecutionResult:
        self.calls.append((target_pool_id, delta_amount))
        return ExecutionResult(success=True, detail="recorded")


def _make_path() -> PathConfig:
    return PathConfig(
        path_id="XLM-USDC-yXLM",
        hops=["XLM", "USDC", "yXLM"],
        pool_ids=["pool-xlm-usdc", "pool-usdc-yxlm"],
    )


def _initial_state(path: PathConfig) -> dict:
    return {
        "run_id": str(uuid.uuid4()),
        "path": path,
        "pool_history": {},
        "signals": {},
        "risk_assessment": None,
        "decision": None,
        "execution_result": None,
    }


def test_depleting_fixture_pools_trigger_a_drips_call():
    # depletion_rate=0.3 over 10 snapshots guarantees a high depletion ratio (~0.95+)
    # regardless of the fixture's per-step jitter, so the resulting score reliably
    # clears a 0.3 threshold even with a flat (zero-velocity, zero-sentiment) signal.
    settings = Settings(_env_file=None, risk_score_threshold=0.3)
    drips_client = _RecordingDripsClient()
    pool_provider = FixturePoolStateProvider(depletion_rate=0.3)
    graph = build_graph(pool_provider, _FlatSignalProvider(), drips_client, settings)

    final_state = graph.invoke(_initial_state(_make_path()))

    assert final_state["decision"].action == "act"
    assert len(drips_client.calls) == 1


def test_flat_fixture_pools_trigger_no_drips_call():
    settings = Settings(_env_file=None, risk_score_threshold=0.65)
    drips_client = _RecordingDripsClient()
    graph = build_graph(_FlatPoolStateProvider(), _FlatSignalProvider(), drips_client, settings)

    final_state = graph.invoke(_initial_state(_make_path()))

    assert final_state["decision"].action == "no_act"
    assert len(drips_client.calls) == 0
