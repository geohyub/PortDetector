"""On-demand port scanning worker."""

from concurrent.futures import ThreadPoolExecutor

from backend.services.scan_service import scan_tcp_port, scan_udp_port, parse_port_range


class ScanWorker:
    def __init__(self, socketio):
        self._socketio = socketio
        self._executor = ThreadPoolExecutor(max_workers=10)

    def scan(self, ip: str, port_str: str, protocol: str = "tcp"):
        """Start a scan job in background."""
        self._executor.submit(self._do_scan, ip, port_str, protocol)

    def _do_scan(self, ip: str, port_str: str, protocol: str):
        ports = parse_port_range(port_str)
        if not ports:
            self._socketio.emit('scan_complete', {
                'ip': ip, 'open_ports': 0, 'closed_ports': 0, 'total_ports': 0,
                'error': 'No valid ports specified',
            })
            return

        scan_fn = scan_tcp_port if protocol == "tcp" else scan_udp_port
        open_count = 0
        closed_count = 0

        self._socketio.emit('scan_progress', {
            'ip': ip, 'total': len(ports), 'scanned': 0, 'status': 'scanning',
        })

        for i, port in enumerate(ports):
            result = scan_fn(ip, port)
            self._socketio.emit('scan_result', result.to_dict())

            if result.state == "open":
                open_count += 1
            else:
                closed_count += 1

            if (i + 1) % 10 == 0 or i == len(ports) - 1:
                self._socketio.emit('scan_progress', {
                    'ip': ip, 'total': len(ports), 'scanned': i + 1,
                    'status': 'scanning',
                })

        self._socketio.emit('scan_complete', {
            'ip': ip,
            'open_ports': open_count,
            'closed_ports': closed_count,
            'total_ports': len(ports),
        })
