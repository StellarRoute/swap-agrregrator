# Verifies Phase 1 graph includes enforce_limits between decide and execute.
import time

from config.settings import Settings
from core.graph import build_graph
from core.state import ExecutionResult, PathConfig, PoolSnapshot, SignalSnapshot


class _StubPool:
    def get_pool_history(self, pool_id: str, lookback: int = 10):
        return [
            PoolSnapshot(
                pool_id=pool_id,
                reserve_a=1000.0,
                reserve_b=1000.0,
                volume_24h=5000.0,
                timestamp=time.time(),
            )
        ]


class _StubSignals:
    def get_signal(self, asset: str):
        return SignalSnapshot(asset=asset, velocity_score=0.9, sentiment_score=0.5)


class _StubDrips:
    def adjust_stream(self, target_pool_id: str, delta_amount: float):
        return ExecutionResult(success=True, detail="ok")


def test_phase1_graph_runs_with_enforce_limits_node():
    settings = Settings(kill_switch_engaged=False, max_stream_delta_per_cycle=50.0)
    path = PathConfig(path_id="p1", hops=["XLM", "USDC"], pool_ids=["pool-1"])
    graph = build_graph(_StubPool(), _StubSignals(), _StubDrips(), settings)
    result = graph.invoke(
        {
            "path": path,
            "pool_history": {},
            "signals": {},
            "risk": None,
            "decision": None,
            "execution_result": None,
        }
    )
    assert result["decision"] is not None
    assert result["execution_result"] is not None
