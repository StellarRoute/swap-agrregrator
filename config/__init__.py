# Marks config as a package and re-exports the shared Settings singleton.
from config.settings import Settings, get_settings

__all__ = ["Settings", "get_settings"]
