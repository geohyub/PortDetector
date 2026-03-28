"""Uptime calculation service — computes device availability from history logs."""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List

from backend.utils.monitoring_presenter import (
    build_report_action,
    build_report_reason,
    derive_report_severity,
    importance_weight,
    severity_rank,
)


class UptimeService:
    def __init__(self, log_service):
        self._log_service = log_service

    def calculate_uptime(self, hours: int = 24) -> Dict[str, dict]:
        """Calculate uptime percentage for each device over the last N hours.

        Returns: {device_id: {uptime_pct, total_mins, up_mins, down_mins,
                              disconnects, avg_rtt, status_changes}}
        """
        entries = self._log_service.get_all_entries()
        if not entries:
            return {}

        now = datetime.now()
        cutoff = now - timedelta(hours=hours)

        # Filter and group by device
        device_events = defaultdict(list)
        for entry in entries:
            ts_str = entry.get('timestamp', '')
            try:
                ts = datetime.fromisoformat(ts_str)
            except (ValueError, TypeError):
                continue
            if ts < cutoff:
                continue
            device_events[entry.get('device_id', '')].append({
                'timestamp': ts,
                'event': entry.get('event', ''),
                'rtt_ms': entry.get('rtt_ms'),
            })

        results = {}
        total_minutes = hours * 60

        for dev_id, events in device_events.items():
            events.sort(key=lambda x: x['timestamp'])

            up_minutes = 0
            down_minutes = 0
            disconnect_count = 0
            rtt_values = []
            status_changes = len(events)

            # Walk through events to compute up/down time
            prev_event = None
            prev_time = cutoff

            for ev in events:
                elapsed = (ev['timestamp'] - prev_time).total_seconds() / 60

                if prev_event is None:
                    # Assume up before first event
                    up_minutes += elapsed
                elif prev_event in ('connected',):
                    up_minutes += elapsed
                else:
                    down_minutes += elapsed

                if ev['event'] == 'disconnected':
                    disconnect_count += 1
                if ev.get('rtt_ms') is not None:
                    rtt_values.append(ev['rtt_ms'])

                prev_event = ev['event']
                prev_time = ev['timestamp']

            # Time after last event until now
            remaining = (now - prev_time).total_seconds() / 60
            if prev_event in ('connected', None):
                up_minutes += remaining
            else:
                down_minutes += remaining

            uptime_pct = (up_minutes / total_minutes * 100) if total_minutes > 0 else 0
            avg_rtt = sum(rtt_values) / len(rtt_values) if rtt_values else None

            results[dev_id] = {
                'uptime_pct': round(min(uptime_pct, 100), 1),
                'total_mins': round(total_minutes, 1),
                'up_mins': round(up_minutes, 1),
                'down_mins': round(down_minutes, 1),
                'disconnects': disconnect_count,
                'avg_rtt': round(avg_rtt, 1) if avg_rtt is not None else None,
                'status_changes': status_changes,
            }

        return results

    def generate_report_data(self, devices: list, hours: int = 24,
                             delay_threshold_ms: int = 200) -> List[dict]:
        """Generate report rows for Excel export."""
        uptime_data = self.calculate_uptime(hours)
        rows = []
        for dev in devices:
            dev_id = dev.id if hasattr(dev, 'id') else dev.get('id', '')
            name = dev.name if hasattr(dev, 'name') else dev.get('name', '')
            ip = dev.ip if hasattr(dev, 'ip') else dev.get('ip', '')
            cat = dev.category if hasattr(dev, 'category') else dev.get('category', '')
            importance = getattr(dev, 'importance', None) if hasattr(dev, 'importance') else dev.get('importance', 'standard')
            ports = list(dev.ports) if hasattr(dev, 'ports') else dev.get('ports', [])
            description = getattr(dev, 'description', '') if hasattr(dev, 'description') else dev.get('description', '')

            stats = uptime_data.get(dev_id, {
                'uptime_pct': 100.0, 'total_mins': hours * 60,
                'up_mins': hours * 60, 'down_mins': 0,
                'disconnects': 0, 'avg_rtt': None, 'status_changes': 0,
            })
            severity = derive_report_severity(
                stats['uptime_pct'],
                stats['disconnects'],
                stats['avg_rtt'],
                importance,
                delay_threshold_ms,
                stats['status_changes'],
            )

            rows.append({
                'device_id': dev_id,
                'name': name,
                'ip': ip,
                'category': cat,
                'importance': importance,
                'ports': ports,
                'description': description,
                'report_severity': severity,
                'report_summary': build_report_reason(
                    stats['uptime_pct'],
                    stats['disconnects'],
                    stats['avg_rtt'],
                    stats['status_changes'],
                    delay_threshold_ms,
                ),
                'report_action': build_report_action(
                    severity,
                    ports,
                    stats['disconnects'],
                    stats['avg_rtt'],
                    delay_threshold_ms,
                ),
                **stats,
            })

        rows.sort(
            key=lambda row: (
                -severity_rank(row.get('report_severity')),
                -importance_weight(row.get('importance')),
                row.get('name', '').lower(),
            )
        )
        return rows
