"""Network map service — topology data, layout persistence, device type inference."""

import json
import os
import re
import socket
import subprocess
import uuid
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional


@dataclass
class MapNode:
    """A single node in the network topology."""
    id: str
    ip: str
    hostname: str = ""
    mac: str = ""
    rtt_ms: Optional[int] = None
    open_ports: List[int] = field(default_factory=list)
    device_type: str = "unknown"   # router, switch, server, workstation, marine, unknown
    user_label: str = ""
    online: bool = True
    x: float = 0.0
    y: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> 'MapNode':
        return cls(
            id=d.get('id', str(uuid.uuid4())[:8]),
            ip=d.get('ip', ''),
            hostname=d.get('hostname', ''),
            mac=d.get('mac', ''),
            rtt_ms=d.get('rtt_ms'),
            open_ports=d.get('open_ports', []),
            device_type=d.get('device_type', 'unknown'),
            user_label=d.get('user_label', ''),
            online=d.get('online', True),
            x=d.get('x', 0.0),
            y=d.get('y', 0.0),
        )


def infer_device_type(ip: str, open_ports: List[int], hostname: str) -> str:
    """Infer device type from open ports and hostname patterns."""
    port_set = set(open_ports)

    # Router/gateway: common management ports
    if port_set & {23, 161, 179, 8291}:
        return "router"
    # Check if it's the gateway (.1 or .254)
    last_octet = ip.split('.')[-1] if '.' in ip else ''
    if last_octet in ('1', '254') and port_set & {80, 443, 22, 23}:
        return "router"

    # Server: web/database/SSH
    server_ports = {22, 80, 443, 3306, 5432, 8080, 8443, 3389, 445, 139}
    if len(port_set & server_ports) >= 2:
        return "server"

    # Marine equipment: common NMEA/hydrographic ports
    marine_ports = {4001, 4002, 4003, 5000, 5001, 5002, 5017, 2947, 10001, 10002, 10110}
    if port_set & marine_ports:
        return "marine"

    # Hostname patterns — marine keywords first (they may contain 'server' as suffix)
    hn = (hostname or '').lower()
    marine_keywords = (
        'mbes', 'mru', 'gyro', 'gps', 'dgnss', 'svp', 'usbl', 'mag',
        'sparker', 'sss', 'sbp', 'echosounder', 'posmv', 'cnav',
        'seapath', 'phins', 'octans', 'hypack', 'qinsy',
    )
    if any(k in hn for k in marine_keywords):
        return "marine"
    if any(k in hn for k in ('router', 'gateway', 'gw', 'fw', 'firewall')):
        return "router"
    if any(k in hn for k in ('switch', 'sw')):
        return "switch"
    if any(k in hn for k in ('srv', 'server', 'nas', 'dc')):
        return "server"

    # Workstation: RDP or common ports
    if 3389 in port_set or 135 in port_set:
        return "workstation"

    if open_ports:
        return "workstation"
    return "unknown"


def get_mac_address(ip: str) -> str:
    """Get MAC address from ARP cache (Windows)."""
    try:
        result = subprocess.run(
            ["arp", "-a", ip],
            capture_output=True, text=True, timeout=3,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        for line in result.stdout.splitlines():
            match = re.search(r'([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}', line)
            if match:
                return match.group(0).replace('-', ':').lower()
    except Exception:
        pass
    return ""


def quick_port_scan(ip: str, ports: List[int], timeout: float = 0.3) -> List[int]:
    """Quick scan of common ports. Returns list of open ports."""
    open_ports = []
    for port in ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            if sock.connect_ex((ip, port)) == 0:
                open_ports.append(port)
            sock.close()
        except OSError:
            pass
    return open_ports


# Common ports to quick-scan for device type inference
COMMON_PORTS = [
    22, 23, 80, 135, 139, 161, 179, 443, 445, 993,
    2947, 3306, 3389, 4001, 4002, 4003, 5000, 5001, 5002, 5017,
    5432, 8080, 8291, 8443, 10001, 10002, 10110,
]


class NetworkMapService:
    """Manages topology data and layout persistence."""

    def __init__(self, data_dir: str):
        self._data_dir = data_dir
        self._layouts_dir = os.path.join(data_dir, 'layouts')
        os.makedirs(self._layouts_dir, exist_ok=True)

    def save_layout(self, name: str, nodes: List[MapNode]) -> str:
        """Save node positions + labels to a JSON file."""
        safe_name = re.sub(r'[^\w\-.]', '_', name)
        if not safe_name.endswith('.json'):
            safe_name += '.json'
        path = os.path.join(self._layouts_dir, safe_name)

        data = {
            'name': name,
            'nodes': [n.to_dict() for n in nodes],
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return path

    def load_layout(self, filename: str) -> List[MapNode]:
        """Load layout from file. Returns list of MapNodes."""
        path = os.path.join(self._layouts_dir, filename)
        if not os.path.exists(path):
            return []
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return [MapNode.from_dict(d) for d in data.get('nodes', [])]

    def list_layouts(self) -> List[dict]:
        """List available layouts."""
        layouts = []
        if not os.path.exists(self._layouts_dir):
            return layouts
        for fname in sorted(os.listdir(self._layouts_dir)):
            if fname.endswith('.json'):
                path = os.path.join(self._layouts_dir, fname)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    layouts.append({
                        'filename': fname,
                        'name': data.get('name', fname),
                        'node_count': len(data.get('nodes', [])),
                    })
                except Exception:
                    layouts.append({'filename': fname, 'name': fname, 'node_count': 0})
        return layouts
