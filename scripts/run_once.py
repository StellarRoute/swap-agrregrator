# CLI entrypoint: runs a single end-to-end StellarHydra cycle for one configured path
# and prints the resulting trace (snapshots -> risk score -> decision -> execution).
from __future__ import annotations

import json
import uuid

from adapters.drips_adapter import MockDripsClient
from adapters.signal_adapter import MockSignalProvider
from adapters.soroban_adapter import FixturePoolStateProvider
from config.settings import get_settings
from core.graph import build_graph
from core.state import PathConfig


def main() -> None:
    settings = get_settings()

    path = PathConfig(
        path_id="XLM-USDC-yXLM",
        hops=["XLM", "USDC", "yXLM"],
        pool_ids=["pool-xlm-usdc", "pool-usdc-yxlm"],
    )

    pool_provider = FixturePoolStateProvider()
    signal_provider = MockSignalProvider()
    drips_client = MockDripsClient()

    graph = build_graph(pool_provider, signal_provider, drips_client, settings)

    initial_state = {
        "run_id": str(uuid.uuid4()),
        "path": path,
        "pool_history": {},
        "signals": {},
        "risk_assessment": None,
        "decision": None,
        "execution_result": None,
    }

    final_state = graph.invoke(initial_state)

    trace = {
        "run_id": final_state["run_id"],
        "path_id": path.path_id,
        "risk_assessment": final_state["risk_assessment"].model_dump(),
        "decision": final_state["decision"].model_dump(),
        "execution_result": final_state["execution_result"].model_dump(),
    }
    print(json.dumps(trace, indent=2, default=str))


if __name__ == "__main__":
    main()
