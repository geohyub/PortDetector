"""Qt-based subnet discovery worker."""

from PySide6.QtCore import QThread, Signal

from backend.services.discovery_service import discover_subnet, get_local_subnet


class DiscoveryWorkerThread(QThread):
    """Runs subnet discovery in background."""

    progress = Signal(int, int, int)  # scanned, total, found_count
    complete = Signal(list)           # list of {ip, rtt_ms, hostname}

    def __init__(self, subnet_prefix=None, timeout_ms=500):
        super().__init__()
        self._subnet = subnet_prefix or get_local_subnet()
        self._timeout = timeout_ms

    def run(self):
        def on_progress(scanned, total, found):
            self.progress.emit(scanned, total, len(found))

        results = discover_subnet(
            self._subnet, timeout_ms=self._timeout, callback=on_progress
        )
        self.complete.emit(results)
