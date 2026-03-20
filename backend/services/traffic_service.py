"""Per-device traffic monitoring using raw socket packet capture.
Requires administrator privileges on Windows.
Falls back gracefully if not available.
"""

import socket
import struct
import threading
import time
from collections import defaultdict


class TrafficService:
    def __init__(self):
        self._running = False
        self._thread = None
        self._lock = threading.Lock()
        self._available = False

        # Traffic counters: ip -> {bytes_in, bytes_out, packets_in, packets_out}
        self._counters = defaultdict(lambda: {
            'bytes_in': 0, 'bytes_out': 0,
            'packets_in': 0, 'packets_out': 0,
        })
        # Snapshot for rate calculation
        self._prev_snapshot = {}
        self._rates = {}  # ip -> {bps_in, bps_out}
        self._last_snapshot_time = 0

        self._local_ip = self._get_local_ip()
        self._sock = None

    def _get_local_ip(self):
        try:
            import psutil
            for name, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family.name == 'AF_INET' and not addr.address.startswith('127.'):
                        return addr.address
        except Exception:
            pass
        return '0.0.0.0'

    def is_available(self):
        return self._available

    def start(self):
        if self._running:
            return

        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_IP)
            self._sock.bind((self._local_ip, 0))
            self._sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
            # Enable promiscuous mode (receive all packets)
            self._sock.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)
            self._available = True
        except (PermissionError, OSError):
            # Not running as administrator
            self._available = False
            return

        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

        # Rate calculation thread
        self._rate_thread = threading.Thread(target=self._rate_loop, daemon=True)
        self._rate_thread.start()

    def stop(self):
        self._running = False
        if self._sock:
            try:
                self._sock.ioctl(socket.SIO_RCVALL, socket.RCVALL_OFF)
                self._sock.close()
            except Exception:
                pass
        if self._thread:
            self._thread.join(timeout=3)

    def _capture_loop(self):
        while self._running:
            try:
                data = self._sock.recvfrom(65535)[0]
                if len(data) < 20:
                    continue

                # Parse IP header
                ihl = (data[0] & 0x0F) * 4
                total_length = struct.unpack('!H', data[2:4])[0]
                src_ip = socket.inet_ntoa(data[12:16])
                dst_ip = socket.inet_ntoa(data[16:20])

                with self._lock:
                    if dst_ip == self._local_ip:
                        # Incoming traffic from src_ip
                        self._counters[src_ip]['bytes_in'] += total_length
                        self._counters[src_ip]['packets_in'] += 1
                    elif src_ip == self._local_ip:
                        # Outgoing traffic to dst_ip
                        self._counters[dst_ip]['bytes_out'] += total_length
                        self._counters[dst_ip]['packets_out'] += 1

            except (OSError, struct.error):
                if not self._running:
                    break
                time.sleep(0.1)

    def _rate_loop(self):
        """Calculate rates every 3 seconds."""
        while self._running:
            time.sleep(3)
            now = time.time()
            elapsed = now - self._last_snapshot_time if self._last_snapshot_time else 3
            self._last_snapshot_time = now

            with self._lock:
                current = {}
                for ip, c in self._counters.items():
                    current[ip] = dict(c)

            new_rates = {}
            for ip, cur in current.items():
                prev = self._prev_snapshot.get(ip, {
                    'bytes_in': 0, 'bytes_out': 0,
                    'packets_in': 0, 'packets_out': 0,
                })
                new_rates[ip] = {
                    'bps_in': max(0, (cur['bytes_in'] - prev['bytes_in']) / elapsed),
                    'bps_out': max(0, (cur['bytes_out'] - prev['bytes_out']) / elapsed),
                    'pps_in': max(0, (cur['packets_in'] - prev['packets_in']) / elapsed),
                    'pps_out': max(0, (cur['packets_out'] - prev['packets_out']) / elapsed),
                }

            self._prev_snapshot = current
            with self._lock:
                self._rates = new_rates

    def get_device_traffic(self, device_ips=None):
        """Get traffic data for specific device IPs."""
        with self._lock:
            result = {}
            ips = device_ips or list(self._counters.keys())
            for ip in ips:
                c = self._counters.get(ip, {
                    'bytes_in': 0, 'bytes_out': 0,
                    'packets_in': 0, 'packets_out': 0,
                })
                r = self._rates.get(ip, {
                    'bps_in': 0, 'bps_out': 0,
                    'pps_in': 0, 'pps_out': 0,
                })
                result[ip] = {
                    'bytes_in': c['bytes_in'],
                    'bytes_out': c['bytes_out'],
                    'packets_in': c['packets_in'],
                    'packets_out': c['packets_out'],
                    'rate_in': r['bps_in'],
                    'rate_out': r['bps_out'],
                }
            return result
