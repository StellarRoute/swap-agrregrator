# CLI entrypoint: starts the Phase 2 continuous multi-path orchestration loop.
from __future__ import annotations

from config.settings import get_settings
from core.orchestrator import Orchestrator
from core.state import PathConfig

TRACKED_PATHS = [
    PathConfig(
        path_id="XLM-USDC-yXLM",
        hops=["XLM", "USDC", "yXLM"],
        pool_ids=["pool-xlm-usdc", "pool-usdc-yxlm"],
    ),
    PathConfig(
        path_id="XLM-AQUA",
        hops=["XLM", "AQUA"],
        pool_ids=["pool-xlm-aqua"],
    ),
]


def main() -> None:
    settings = get_settings()
    orchestrator = Orchestrator(TRACKED_PATHS, settings)
    orchestrator.run_forever()


if __name__ == "__main__":
    main()
