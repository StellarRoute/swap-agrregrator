# Redis-backed kill switch state shared across orchestrator and admin API pods.
from __future__ import annotations

import redis

from config.settings import get_settings


class RedisKillSwitch:
    KEY = "stellarhydra:kill_switch:engaged"

    def __init__(self, redis_url: str | None = None) -> None:
        settings = get_settings()
        self._client = redis.from_url(redis_url or settings.redis_url, decode_responses=True)

    def engage(self) -> None:
        self._client.set(self.KEY, "1")

    def disengage(self) -> None:
        self._client.delete(self.KEY)

    @property
    def engaged(self) -> bool:
        return self._client.get(self.KEY) == "1"
