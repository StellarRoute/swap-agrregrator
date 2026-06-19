# Load tracked path configs from TRACKED_PATHS env string.
from __future__ import annotations

from config.settings import Settings, get_settings, tracked_path_ids
from core.state import PathConfig


def load_tracked_paths(settings: Settings | None = None) -> list[PathConfig]:
    cfg = settings or get_settings()
    paths: list[PathConfig] = []
    for path_id in tracked_path_ids(cfg):
        parts = path_id.upper().split("-")
        if len(parts) < 2:
            continue
        pool_ids = [f"pool-{'-'.join(parts[i : i + 2]).lower()}" for i in range(len(parts) - 1)]
        paths.append(PathConfig(path_id=path_id, hops=parts, pool_ids=pool_ids))
    return paths
