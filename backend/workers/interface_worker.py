"""Network interface status polling worker."""

import threading

from backend.services.interface_service import InterfaceService


class InterfaceWorker:
    def __init__(self, socketio):
        self._socketio = socketio
        self._service = InterfaceService()
        self._stop_event = threading.Event()
        self._thread = None
        self._interval = 3

    def start(self, interval: int = 3):
        self._interval = interval
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)

    def update_interval(self, interval: int):
        self._interval = interval

    def get_interfaces(self):
        return [iface.to_dict() for iface in self._service.get_interfaces()]

    def _run(self):
        while not self._stop_event.is_set():
            try:
                interfaces = self._service.get_interfaces()
                self._socketio.emit('interface_update', {
                    'interfaces': [i.to_dict() for i in interfaces]
                })
            except Exception:
                pass
            self._stop_event.wait(self._interval)
