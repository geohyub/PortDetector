"""Port scanning service."""

import socket
from typing import List

from backend.models.status import PortScanResult


def scan_tcp_port(ip: str, port: int, timeout: float = 1.0) -> PortScanResult:
    """Scan a single TCP port."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()

        if result == 0:
            state = "open"
        else:
            state = "closed"

        try:
            service = socket.getservbyport(port, 'tcp')
        except OSError:
            service = ""

        return PortScanResult(ip=ip, port=port, protocol="tcp", state=state, service_name=service)
    except socket.timeout:
        return PortScanResult(ip=ip, port=port, protocol="tcp", state="filtered", service_name="")
    except OSError:
        return PortScanResult(ip=ip, port=port, protocol="tcp", state="closed", service_name="")


def scan_udp_port(ip: str, port: int, timeout: float = 2.0) -> PortScanResult:
    """Scan a single UDP port (limited reliability)."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        sock.sendto(b'', (ip, port))
        try:
            sock.recvfrom(1024)
            state = "open"
        except socket.timeout:
            state = "open|filtered"
        except ConnectionResetError:
            state = "closed"
        sock.close()

        try:
            service = socket.getservbyport(port, 'udp')
        except OSError:
            service = ""

        return PortScanResult(ip=ip, port=port, protocol="udp", state=state, service_name=service)
    except OSError:
        return PortScanResult(ip=ip, port=port, protocol="udp", state="closed", service_name="")


def parse_port_range(port_str: str) -> List[int]:
    """Parse port string like '80,443,8080-8090' into list of ports."""
    ports = []
    for part in port_str.split(','):
        part = part.strip()
        if '-' in part:
            try:
                start, end = part.split('-', 1)
                start, end = int(start), int(end)
                if 1 <= start <= 65535 and 1 <= end <= 65535:
                    ports.extend(range(start, end + 1))
            except ValueError:
                continue
        else:
            try:
                p = int(part)
                if 1 <= p <= 65535:
                    ports.append(p)
            except ValueError:
                continue
    return sorted(set(ports))
