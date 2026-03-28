"""Shared monitoring labels, severity rules, and operator-facing text."""

from __future__ import annotations

from datetime import datetime
from typing import Iterable


IMPORTANCE_LEVELS = ("critical", "high", "standard", "optional")

IMPORTANCE_LABELS = {
    "critical": "Critical",
    "high": "Important",
    "standard": "Standard",
    "optional": "Optional",
}

IMPORTANCE_WEIGHTS = {
    "critical": 4,
    "high": 3,
    "standard": 2,
    "optional": 1,
}

SEVERITY_LABELS = {
    "stable": "Stable",
    "info": "Info",
    "advisory": "Advisory",
    "warning": "Warning",
    "critical": "Critical",
    "emergency": "Emergency",
}

SEVERITY_ORDER = {
    "stable": 0,
    "info": 1,
    "advisory": 2,
    "warning": 3,
    "critical": 4,
    "emergency": 5,
}


def normalize_importance(value: str | None) -> str:
    value = (value or "standard").strip().lower()
    return value if value in IMPORTANCE_LEVELS else "standard"


def importance_label(value: str | None) -> str:
    return IMPORTANCE_LABELS[normalize_importance(value)]


def importance_weight(value: str | None) -> int:
    return IMPORTANCE_WEIGHTS[normalize_importance(value)]


def severity_label(value: str | None) -> str:
    return SEVERITY_LABELS.get(value or "", "Info")


def severity_rank(value: str | None) -> int:
    return SEVERITY_ORDER.get(value or "", 0)


def build_status_label(status: str | None) -> str:
    status = (status or "unknown").lower()
    if status == "connected":
        return "Stable"
    if status == "delayed":
        return "High latency"
    if status == "disconnected":
        return "No response"
    return "Waiting for data"


def build_status_reason(status: str | None, rtt_ms: int | None, delay_threshold_ms: int) -> str:
    status = (status or "unknown").lower()
    if status == "connected":
        if rtt_ms is not None:
            return f"Ping responded in {rtt_ms:,} ms."
        return "Ping responded normally."
    if status == "delayed":
        if rtt_ms is not None:
            return (
                f"Ping responded in {rtt_ms:,} ms, above the "
                f"{delay_threshold_ms:,} ms delay threshold."
            )
        return f"Response arrived slower than the {delay_threshold_ms:,} ms delay threshold."
    if status == "disconnected":
        return "No ping reply was received during the latest monitoring cycle."
    return "Waiting for the first monitoring result."


def build_ports_text(ports: Iterable[int] | None) -> str:
    ports = list(ports or [])
    if not ports:
        return "No reference ports"
    return ", ".join(str(port) for port in ports)


def build_action_text(status: str | None, ports: Iterable[int] | None, fail_count: int) -> str:
    status = (status or "unknown").lower()
    port_text = build_ports_text(ports)
    if status == "connected":
        if ports:
            return (
                f"Host reachability is healthy. If the application still feels down, "
                f"open Scanner and verify reference ports {port_text}."
            )
        return "Reachability is healthy. Keep observing only if operators still report intermittent issues."
    if status == "delayed":
        if fail_count >= 3:
            if ports:
                return (
                    f"Latency has stayed high for several checks. Review interface load and "
                    f"verify reference ports {port_text} before escalating."
                )
            return "Latency has stayed high for several checks. Review interface load before escalating."
        if ports:
            return f"Watch another cycle or verify reference ports {port_text} if the service feels unstable."
        return "Watch another cycle before escalating."
    if status == "disconnected":
        if ports:
            return (
                f"Check power, cabling, routing, or VPN first. Once ping recovers, verify "
                f"reference ports {port_text}."
            )
        return "Check power, cabling, routing, or VPN state first."
    return "Waiting for monitoring data."


def derive_runtime_severity(status: str | None, importance: str | None, fail_count: int) -> str:
    status = (status or "unknown").lower()
    importance = normalize_importance(importance)

    if status == "connected":
        return "stable"

    if status == "delayed":
        if fail_count >= 6:
            return "critical"
        if fail_count >= 3:
            return "critical" if importance in ("critical", "high") else "warning"
        return "warning" if importance == "critical" else "advisory"

    if status == "disconnected":
        if fail_count >= 10:
            return "emergency"
        if fail_count >= 3 or importance in ("critical", "high"):
            return "critical"
        return "warning"

    return "info"


def derive_event_severity(event: str | None, importance: str | None) -> str:
    event = (event or "").lower()
    importance = normalize_importance(importance)

    if event == "connected":
        return "info"
    if event == "delayed":
        return "warning" if importance in ("critical", "high") else "advisory"
    if event == "disconnected":
        return "critical" if importance != "optional" else "warning"
    return "info"


def derive_report_severity(
    uptime_pct: float,
    disconnects: int,
    avg_rtt: float | None,
    importance: str | None,
    delay_threshold_ms: int,
    status_changes: int = 0,
) -> str:
    importance = normalize_importance(importance)
    latency_high = avg_rtt is not None and avg_rtt > delay_threshold_ms
    repeated_disconnects = disconnects >= (2 if importance == "critical" else 3 if importance == "high" else 4)

    if uptime_pct < 95 or repeated_disconnects:
        return "critical" if importance != "optional" else "warning"

    if latency_high and (importance in ("critical", "high") or avg_rtt >= delay_threshold_ms * 1.5):
        return "warning"

    if disconnects > 0 or uptime_pct < 99 or latency_high or status_changes >= 6:
        return "warning" if importance in ("critical", "high") else "advisory"

    return "stable"


def build_report_reason(
    uptime_pct: float,
    disconnects: int,
    avg_rtt: float | None,
    status_changes: int,
    delay_threshold_ms: int,
) -> str:
    parts = [f"{uptime_pct:.1f}% uptime"]
    if disconnects:
        parts.append(f"{disconnects} disconnect(s)")
    if avg_rtt is not None:
        if avg_rtt > delay_threshold_ms:
            parts.append(f"average RTT {avg_rtt:,.1f} ms above threshold")
        else:
            parts.append(f"average RTT {avg_rtt:,.1f} ms")
    if status_changes:
        parts.append(f"{status_changes} state changes")
    return ", ".join(parts) + "."


def build_report_action(
    severity: str,
    ports: Iterable[int] | None,
    disconnects: int,
    avg_rtt: float | None,
    delay_threshold_ms: int,
) -> str:
    port_text = build_ports_text(ports)

    if severity == "stable":
        return "No immediate action. Keep this device in normal monitoring."

    if avg_rtt is not None and avg_rtt > delay_threshold_ms and disconnects == 0:
        if ports:
            return f"Watch latency and verify reference ports {port_text} if operators feel service slowdown."
        return "Watch latency trend and review interface load if operators feel slowdown."

    if ports:
        return (
            f"Review the disconnect windows first, then verify reference ports {port_text} "
            f"once host reachability is stable."
        )
    return "Review repeated disconnect windows and upstream network/power state."


def format_relative_time(timestamp: str | None, now: datetime | None = None) -> str:
    if not timestamp:
        return "No recent change"

    try:
        ts = datetime.fromisoformat(timestamp)
    except (TypeError, ValueError):
        return timestamp

    now = now or datetime.now()
    seconds = max(int((now - ts).total_seconds()), 0)
    if seconds < 10:
        return "Changed just now"
    if seconds < 60:
        return f"Changed {seconds} sec ago"
    minutes = seconds // 60
    if minutes < 60:
        return f"Changed {minutes} min ago"
    hours = minutes // 60
    if hours < 24:
        return f"Changed {hours} hr ago"
    days = hours // 24
    return f"Changed {days} day(s) ago"
