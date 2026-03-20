"""Subnet auto-discovery service."""

import socket
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from backend.services.ping_service import ping


def discover_subnet(subnet_prefix, start=1, end=254, timeout_ms=500, callback=None):
    """Scan a subnet for active hosts. e.g. subnet_prefix='192.168.1'"""
    found = []
    total = end - start + 1

    def check_host(i):
        ip = "{}.{}".format(subnet_prefix, i)
        success, rtt = ping(ip, timeout_ms=timeout_ms)
        if success:
            try:
                hostname = socket.getfqdn(ip)
                if hostname == ip:
                    hostname = ""
            except Exception:
                hostname = ""
            return {"ip": ip, "rtt_ms": rtt, "hostname": hostname}
        return None

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {}
        for i in range(start, end + 1):
            f = executor.submit(check_host, i)
            futures[f] = i

        scanned = 0
        for future in as_completed(futures):
            scanned += 1
            result = future.result()
            if result:
                found.append(result)
            if callback and scanned % 10 == 0:
                callback(scanned, total, found)

    found.sort(key=lambda x: list(map(int, x['ip'].split('.'))))
    return found


def get_local_subnet():
    """Get the local machine's subnet prefix."""
    import psutil
    for name, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family.name == 'AF_INET' and not addr.address.startswith('127.'):
                parts = addr.address.split('.')
                return '.'.join(parts[:3])
    return '192.168.1'
