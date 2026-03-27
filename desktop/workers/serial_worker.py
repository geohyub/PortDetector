"""Qt-based serial port monitoring worker."""

from PySide6.QtCore import QThread, Signal

from backend.services.serial_service import list_serial_ports, test_serial_port


class SerialWorkerThread(QThread):
    """Polls serial ports at regular intervals."""

    update = Signal(list)  # list of {port, status, message, description}

    def __init__(self, ports_to_monitor: list = None, interval: int = 5):
        super().__init__()
        self._ports = ports_to_monitor or []
        self._interval = interval
        self._running = True

    def set_ports(self, ports: list):
        self._ports = ports

    def set_interval(self, interval: int):
        self._interval = interval

    def stop(self):
        self._running = False

    def run(self):
        while self._running:
            results = []

            # List available ports
            available = {p['port']: p for p in list_serial_ports()}

            for port_name in self._ports:
                info = available.get(port_name, {})
                success, message = test_serial_port(port_name)

                results.append({
                    'port': port_name,
                    'status': 'connected' if success else 'disconnected',
                    'message': message,
                    'description': info.get('description', ''),
                    'manufacturer': info.get('manufacturer', ''),
                })

            # Also report any available ports not being monitored
            for port_name, info in available.items():
                if port_name not in self._ports:
                    results.append({
                        'port': port_name,
                        'status': 'available',
                        'message': 'Not monitored',
                        'description': info.get('description', ''),
                        'manufacturer': info.get('manufacturer', ''),
                    })

            if results:
                self.update.emit(results)

            for _ in range(self._interval * 10):
                if not self._running:
                    break
                self.msleep(100)
