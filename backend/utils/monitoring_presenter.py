"""Shared monitoring labels, severity rules, and operator-facing text."""

from __future__ import annotations

from datetime import datetime
from typing import Iterable

from desktop.i18n import t


IMPORTANCE_LEVELS = ("critical", "high", "standard", "optional")

IMPORTANCE_WEIGHTS = {
    "critical": 4,
    "high": 3,
    "standard": 2,
    "optional": 1,
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
    key = normalize_importance(value)
    return t(f"importance.{key}")


def importance_weight(value: str | None) -> int:
    return IMPORTANCE_WEIGHTS[normalize_importance(value)]


def severity_label(value: str | None) -> str:
    key = value or "info"
    return t(f"severity.{key}")


def severity_rank(value: str | None) -> int:
    return SEVERITY_ORDER.get(value or "", 0)


def build_status_label(status: str | None) -> str:
    status = (status or "unknown").lower()
    if status == "connected":
        return t("status.connected")
    if status == "delayed":
        return t("status.delayed")
    if status == "disconnected":
        return t("status.disconnected")
    return t("status.waiting")


def build_status_reason(status: str | None, rtt_ms: int | None, delay_threshold_ms: int) -> str:
    status = (status or "unknown").lower()
    if status == "connected":
        if rtt_ms is not None:
            return t("reason.connected", rtt=f"{rtt_ms:,}")
        return t("reason.connected_ok")
    if status == "delayed":
        if rtt_ms is not None:
            return t("reason.delayed", rtt=f"{rtt_ms:,}", threshold=f"{delay_threshold_ms:,}")
        return t("reason.delayed_no_rtt", threshold=f"{delay_threshold_ms:,}")
    if status == "disconnected":
        return t("reason.disconnected")
    return t("reason.unknown")


def build_ports_text(ports: Iterable[int] | None) -> str:
    ports = list(ports or [])
    if not ports:
        return t("report.no_ports")
    return ", ".join(str(port) for port in ports)


def build_action_text(status: str | None, ports: Iterable[int] | None, fail_count: int) -> str:
    status = (status or "unknown").lower()
    port_list = list(ports or [])
    port_text = ", ".join(str(p) for p in port_list)

    if status == "connected":
        if port_list:
            return t("action.connected_ports", ports=port_text)
        return t("action.connected_no_ports")
    if status == "delayed":
        if fail_count >= 3:
            if port_list:
                return t("action.delayed_long_ports", ports=port_text)
            return t("action.delayed_long_no_ports")
        if port_list:
            return t("action.delayed_short_ports", ports=port_text)
        return t("action.delayed_short_no_ports")
    if status == "disconnected":
        if port_list:
            return t("action.disconnected_ports", ports=port_text)
        return t("action.disconnected_no_ports")
    return t("action.waiting")


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
    parts = [t("report.uptime", pct=f"{uptime_pct:.1f}")]
    if disconnects:
        parts.append(t("report.disconnects", n=disconnects))
    if avg_rtt is not None:
        if avg_rtt > delay_threshold_ms:
            parts.append(t("report.avg_rtt_above", rtt=f"{avg_rtt:,.1f}"))
        else:
            parts.append(t("report.avg_rtt_normal", rtt=f"{avg_rtt:,.1f}"))
    if status_changes:
        parts.append(t("report.state_changes", n=status_changes))
    return ", ".join(parts) + "."


def build_report_action(
    severity: str,
    ports: Iterable[int] | None,
    disconnects: int,
    avg_rtt: float | None,
    delay_threshold_ms: int,
) -> str:
    port_list = list(ports or [])
    port_text = ", ".join(str(p) for p in port_list)

    if severity == "stable":
        return t("report.action_stable")

    if avg_rtt is not None and avg_rtt > delay_threshold_ms and disconnects == 0:
        if port_list:
            return t("report.action_latency", ports=port_text)
        return t("report.action_latency_no_ports")

    if port_list:
        return t("report.action_disconnects", ports=port_text)
    return t("report.action_disconnects_no_ports")


def format_relative_time(timestamp: str | None, now: datetime | None = None) -> str:
    if not timestamp:
        return t("time.no_change")

    try:
        ts = datetime.fromisoformat(timestamp)
    except (TypeError, ValueError):
        return timestamp

    now = now or datetime.now()
    seconds = max(int((now - ts).total_seconds()), 0)
    if seconds < 10:
        return t("time.just_now")
    if seconds < 60:
        return t("time.sec_ago", n=seconds)
    minutes = seconds // 60
    if minutes < 60:
        return t("time.min_ago", n=minutes)
    hours = minutes // 60
    if hours < 24:
        return t("time.hr_ago", n=hours)
    days = hours // 24
    return t("time.day_ago", n=days)
