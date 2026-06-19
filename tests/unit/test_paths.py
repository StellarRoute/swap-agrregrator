# Unit tests for tracked path loading from settings.
from config.paths import load_tracked_paths
from config.settings import Settings


def test_load_tracked_paths_parses_env_string():
    settings = Settings(tracked_paths="xlm-usdc,yxlm-xlm")
    paths = load_tracked_paths(settings)
    assert len(paths) == 2
    assert paths[0].hops == ["XLM", "USDC"]
