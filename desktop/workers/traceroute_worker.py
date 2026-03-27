"""Qt-based traceroute worker."""

from PySide6.QtCore import QThread, Signal

from backend.services.traceroute_service import traceroute


class TracerouteWorkerThread(QThread):
    """Runs traceroute in background."""

    complete = Signal(list)  # list of hop dicts

    def __init__(self, ip: str, max_hops: int = 30):
        super().__init__()
        self._ip = ip
        self._max_hops = max_hops

    def run(self):
        hops = traceroute(self._ip, max_hops=self._max_hops)
        self.complete.emit(hops)
