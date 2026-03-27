"""Qt-based port scan worker — replaces SocketIO ScanWorker."""

from PySide6.QtCore import QObject, QThread, Signal

from backend.services.scan_service import scan_tcp_port, scan_udp_port, parse_port_range


class ScanWorkerThread(QThread):
    """Runs a port scan in background thread."""

    progress = Signal(dict)    # {ip, total, scanned, status}
    result = Signal(dict)      # single PortScanResult dict
    complete = Signal(dict)    # {ip, open_ports, closed_ports, total_ports}

    def __init__(self, ip: str, port_str: str, protocol: str = "tcp"):
        super().__init__()
        self._ip = ip
        self._port_str = port_str
        self._protocol = protocol
        self._running = True

    def stop(self):
        self._running = False

    def run(self):
        ports = parse_port_range(self._port_str)
        if not ports:
            self.complete.emit({
                'ip': self._ip, 'open_ports': 0, 'closed_ports': 0,
                'total_ports': 0, 'error': 'No valid ports specified',
            })
            return

        scan_fn = scan_tcp_port if self._protocol == "tcp" else scan_udp_port
        open_count = 0
        closed_count = 0

        self.progress.emit({
            'ip': self._ip, 'total': len(ports), 'scanned': 0, 'status': 'scanning',
        })

        for i, port in enumerate(ports):
            if not self._running:
                break

            res = scan_fn(self._ip, port)
            self.result.emit(res.to_dict())

            if res.state == "open":
                open_count += 1
            else:
                closed_count += 1

            if (i + 1) % 10 == 0 or i == len(ports) - 1:
                self.progress.emit({
                    'ip': self._ip, 'total': len(ports), 'scanned': i + 1,
                    'status': 'scanning',
                })

        self.complete.emit({
            'ip': self._ip,
            'open_ports': open_count,
            'closed_ports': closed_count,
            'total_ports': len(ports),
        })
