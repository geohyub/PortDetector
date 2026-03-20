"""Status result data models."""

from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class PingResult:
    device_id: str
    ip: str
    status: str  # "connected" | "disconnected" | "delayed"
    rtt_ms: Optional[int] = None
    timestamp: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class PortScanResult:
    ip: str
    port: int
    protocol: str  # "tcp" | "udp"
    state: str  # "open" | "closed" | "filtered"
    service_name: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class InterfaceStatus:
    name: str
    is_up: bool
    speed_mbps: int
    ipv4: Optional[str] = None
    bytes_sent: int = 0
    bytes_recv: int = 0
    throughput_in: float = 0.0  # bytes/sec
    throughput_out: float = 0.0

    def to_dict(self):
        return asdict(self)
