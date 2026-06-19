# CLI entrypoint: starts the Phase 2 continuous multi-path orchestration loop.
from __future__ import annotations

from config.paths import load_tracked_paths
from config.settings import get_settings
from core.orchestrator import Orchestrator

DEFAULT_TRACKED_PATHS = load_tracked_paths()


def main() -> None:
    settings = get_settings()
    paths = load_tracked_paths(settings) or DEFAULT_TRACKED_PATHS
    orchestrator = Orchestrator(paths, settings)
    orchestrator.run_forever()


if __name__ == "__main__":
    main()
