"""Network map workers — subnet scan + port scan + status monitor (QThread)."""

from __future__ import annotations

import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

from PySide6.QtCore import QThread, Signal

from backend.services.ping_service import ping
from backend.services.network_map_service import (
    MapNode, get_mac_address, quick_port_scan, infer_device_type, COMMON_PORTS,
)


class MapScanWorkerThread(QThread):
    """Full subnet scan: ping + MAC + port scan + device type inference."""

    progress = Signal(int, int)     # scanned, total
    node_found = Signal(dict)       # single MapNode dict as discovered
    complete = Signal(list)         # all MapNode dicts

    def __init__(self, subnet_prefix: str, timeout_ms: int = 500):
        super().__init__()
        self._subnet = subnet_prefix
        self._timeout = timeout_ms
        self._running = True

    def stop(self):
        self._running = False

    def run(self):
        nodes = []
        total = 254

        def scan_host(i):
            if not self._running:
                return None
            ip = f"{self._subnet}.{i}"
            success, rtt = ping(ip, timeout_ms=self._timeout)
            if not success:
                return None

            # Get hostname
            try:
                hostname = socket.getfqdn(ip)
                if hostname == ip:
                    hostname = ""
            except Exception:
                hostname = ""

            # Get MAC from ARP cache
            mac = get_mac_address(ip)

            # Quick port scan for type inference
            open_ports = quick_port_scan(ip, COMMON_PORTS, timeout=0.3)

            # Infer device type
            device_type = infer_device_type(ip, open_ports, hostname)

            return MapNode(
                id=f"node_{ip.replace('.', '_')}",
                ip=ip,
                hostname=hostname,
                mac=mac,
                rtt_ms=rtt,
                open_ports=open_ports,
                device_type=device_type,
                online=True,
            )

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = {}
            for i in range(1, 255):
                f = executor.submit(scan_host, i)
                futures[f] = i

            scanned = 0
            for future in as_completed(futures):
                if not self._running:
                    break
                scanned += 1
                if scanned % 5 == 0:
                    self.progress.emit(scanned, total)

                result = future.result()
                if result:
                    node_dict = result.to_dict()
                    nodes.append(node_dict)
                    self.node_found.emit(node_dict)

        self.progress.emit(total, total)
        nodes.sort(key=lambda n: list(map(int, n['ip'].split('.'))))
        self.complete.emit(nodes)


class MapPingWorkerThread(QThread):
    """Periodic ping monitor for existing map nodes."""

    update = Signal(list)  # list of {ip, online, rtt_ms}

    def __init__(self, interval: int = 10):
        super().__init__()
        self._interval = interval
        self._running = True
        self._ips = []

    def set_ips(self, ips: list):
        self._ips = list(ips)

    def set_interval(self, interval: int):
        self._interval = max(3, interval)

    def stop(self):
        self._running = False

    def run(self):
        while self._running:
            if self._ips:
                results = []
                with ThreadPoolExecutor(max_workers=20) as executor:
                    futures = {executor.submit(ping, ip, 1000): ip for ip in self._ips}
                    for future in as_completed(futures):
                        ip = futures[future]
                        success, rtt = future.result()
                        results.append({'ip': ip, 'online': success, 'rtt_ms': rtt})
                self.update.emit(results)

            # Sleep in small increments so stop() is responsive
            for _ in range(self._interval * 10):
                if not self._running:
                    return
                self.msleep(100)
