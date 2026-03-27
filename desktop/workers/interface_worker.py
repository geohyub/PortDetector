"""Qt-based interface polling worker — replaces SocketIO InterfaceWorker."""

from PySide6.QtCore import QThread, Signal

from backend.services.interface_service import InterfaceService


class InterfaceWorkerThread(QThread):
    """Polls network interfaces at regular intervals."""

    update = Signal(list)  # list of InterfaceStatus dicts

    def __init__(self, interval: int = 3):
        super().__init__()
        self._service = InterfaceService()
        self._interval = interval
        self._running = True

    def set_interval(self, interval: int):
        self._interval = interval

    def stop(self):
        self._running = False

    def get_interfaces(self):
        return [iface.to_dict() for iface in self._service.get_interfaces()]

    def run(self):
        while self._running:
            try:
                interfaces = self._service.get_interfaces()
                self.update.emit([i.to_dict() for i in interfaces])
            except Exception:
                pass

            for _ in range(self._interval * 10):
                if not self._running:
                    break
                self.msleep(100)
