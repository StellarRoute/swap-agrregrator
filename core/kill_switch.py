# Runtime-toggleable kill switch, layered on top of the static settings default so an
# operator can engage/disengage it via the admin API without restarting the process (F8).
from __future__ import annotations

from threading import Lock


class KillSwitch:
    def __init__(self, default_engaged: bool = False) -> None:
        self._lock = Lock()
        self._engaged = default_engaged

    def engage(self) -> None:
        with self._lock:
            self._engaged = True

    def disengage(self) -> None:
        with self._lock:
            self._engaged = False

    @property
    def engaged(self) -> bool:
        with self._lock:
            return self._engaged


kill_switch = KillSwitch()
