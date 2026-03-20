"""Network interface monitoring service."""

from typing import Dict, List

import psutil

from backend.models.status import InterfaceStatus


class InterfaceService:
    def __init__(self):
        self._prev_counters: Dict[str, tuple] = {}

    def get_interfaces(self) -> List[InterfaceStatus]:
        """Get current status of all network interfaces."""
        stats = psutil.net_if_stats()
        addrs = psutil.net_if_addrs()
        counters = psutil.net_io_counters(pernic=True)

        results = []
        for name, st in stats.items():
            ipv4 = None
            if name in addrs:
                for addr in addrs[name]:
                    if addr.family.name == 'AF_INET':
                        ipv4 = addr.address
                        break

            bytes_sent = 0
            bytes_recv = 0
            throughput_in = 0.0
            throughput_out = 0.0

            if name in counters:
                c = counters[name]
                bytes_sent = c.bytes_sent
                bytes_recv = c.bytes_recv

                if name in self._prev_counters:
                    prev_sent, prev_recv = self._prev_counters[name]
                    throughput_out = max(0, bytes_sent - prev_sent)
                    throughput_in = max(0, bytes_recv - prev_recv)

                self._prev_counters[name] = (bytes_sent, bytes_recv)

            results.append(InterfaceStatus(
                name=name,
                is_up=st.isup,
                speed_mbps=st.speed,
                ipv4=ipv4,
                bytes_sent=bytes_sent,
                bytes_recv=bytes_recv,
                throughput_in=throughput_in,
                throughput_out=throughput_out,
            ))

        return results
