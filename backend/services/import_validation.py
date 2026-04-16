"""Validation helpers for imported config and profile payloads."""

from __future__ import annotations

from typing import Any, Dict

from backend.models.device import Device
from config import (
    DEFAULT_DELAY_THRESHOLD_MS,
    DEFAULT_INTERFACE_POLL_INTERVAL,
    DEFAULT_PING_INTERVAL,
    DEFAULT_WEB_PORT,
)

_DEFAULT_SETTINGS = {
    "ping_interval_seconds": DEFAULT_PING_INTERVAL,
    "interface_poll_seconds": DEFAULT_INTERFACE_POLL_INTERVAL,
    "delay_threshold_ms": DEFAULT_DELAY_THRESHOLD_MS,
    "web_port": DEFAULT_WEB_PORT,
    "auto_open_browser": True,
    "alert_enabled": True,
    "sound_enabled": True,
    "escalation_enabled": True,
    "alert_volume": 0.5,
}


def _ensure_mapping(value: Any, label: str) -> Dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _ensure_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    return value


def _ensure_bool(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{label} must be a boolean")
    return value


def _ensure_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a number")
    return float(value)


def validate_device_payload(payload: Any, label: str = "Device") -> Device:
    data = _ensure_mapping(payload, label)

    device = Device.from_dict(data)

    if not isinstance(device.id, str):
        raise ValueError(f"{label} id must be a string")
    if not isinstance(device.name, str):
        raise ValueError(f"{label} name must be a string")
    if not isinstance(device.ip, str):
        raise ValueError(f"{label} ip must be a string")
    if not isinstance(device.category, str):
        raise ValueError(f"{label} category must be a string")
    if not isinstance(device.importance, str):
        raise ValueError(f"{label} importance must be a string")
    if not isinstance(device.description, str):
        raise ValueError(f"{label} description must be a string")
    if not isinstance(device.enabled, bool):
        raise ValueError(f"{label} enabled must be a boolean")
    if not isinstance(device.ports, list):
        raise ValueError(f"{label} ports must be a list")
    if any(isinstance(port, bool) or not isinstance(port, int) for port in device.ports):
        raise ValueError(f"{label} ports must contain integers only")

    errors = device.validate()
    if errors:
        raise ValueError(f"{label}: " + "; ".join(errors))
    return device


def validate_settings_payload(payload: Any) -> Dict[str, Any]:
    data = _ensure_mapping(payload, "Settings")
    normalized = dict(_DEFAULT_SETTINGS)

    if "ping_interval_seconds" in data:
        normalized["ping_interval_seconds"] = _ensure_int(
            data["ping_interval_seconds"], "ping_interval_seconds"
        )
    if "interface_poll_seconds" in data:
        normalized["interface_poll_seconds"] = _ensure_int(
            data["interface_poll_seconds"], "interface_poll_seconds"
        )
    if "delay_threshold_ms" in data:
        normalized["delay_threshold_ms"] = _ensure_int(
            data["delay_threshold_ms"], "delay_threshold_ms"
        )
    if "web_port" in data:
        normalized["web_port"] = _ensure_int(data["web_port"], "web_port")
    if "auto_open_browser" in data:
        normalized["auto_open_browser"] = _ensure_bool(
            data["auto_open_browser"], "auto_open_browser"
        )
    if "alert_enabled" in data:
        normalized["alert_enabled"] = _ensure_bool(data["alert_enabled"], "alert_enabled")
    if "sound_enabled" in data:
        normalized["sound_enabled"] = _ensure_bool(data["sound_enabled"], "sound_enabled")
    if "escalation_enabled" in data:
        normalized["escalation_enabled"] = _ensure_bool(
            data["escalation_enabled"], "escalation_enabled"
        )
    if "alert_volume" in data:
        normalized["alert_volume"] = _ensure_number(data["alert_volume"], "alert_volume")

    return normalized


def validate_config_payload(payload: Any) -> Dict[str, Any]:
    data = _ensure_mapping(payload, "Configuration")

    settings = validate_settings_payload(data.get("settings", {}))

    devices_raw = data.get("devices", [])
    if devices_raw is None:
        devices_raw = []
    if not isinstance(devices_raw, list):
        raise ValueError("Configuration devices must be a list")

    devices = [
        validate_device_payload(device_data, f"Device {index + 1}")
        for index, device_data in enumerate(devices_raw)
    ]

    version = data.get("version", 1)
    if version is not None:
        version = _ensure_int(version, "version")

    return {
        "version": version,
        "settings": settings,
        "devices": [device.to_dict() for device in devices],
    }


def validate_profile_payload(payload: Any) -> Dict[str, Any]:
    data = _ensure_mapping(payload, "Profile")
    config = validate_config_payload(data)

    profile = {
        "version": config["version"],
        "settings": config["settings"],
        "devices": config["devices"],
    }

    for field in ("name", "vessel", "description", "created"):
        if field in data:
            value = data[field]
            if value is None:
                continue
            if not isinstance(value, str):
                raise ValueError(f"Profile {field} must be a string")
            profile[field] = value

    return profile
