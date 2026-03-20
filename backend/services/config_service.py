"""Configuration service for device management and settings."""

import json
import os
import threading
from typing import List, Optional

from backend.models.device import Device
from config import (
    DEFAULT_PING_INTERVAL,
    DEFAULT_INTERFACE_POLL_INTERVAL,
    DEFAULT_DELAY_THRESHOLD_MS,
    DEFAULT_WEB_PORT,
)


class ConfigService:
    def __init__(self, data_dir: str):
        self._lock = threading.RLock()
        self._data_dir = data_dir
        self._config_path = os.path.join(data_dir, 'devices.json')
        self._devices: List[Device] = []
        self._settings = {}
        self._next_id = 1
        self._load()

    def _default_config(self):
        return {
            "version": 1,
            "settings": {
                "ping_interval_seconds": DEFAULT_PING_INTERVAL,
                "interface_poll_seconds": DEFAULT_INTERFACE_POLL_INTERVAL,
                "delay_threshold_ms": DEFAULT_DELAY_THRESHOLD_MS,
                "web_port": DEFAULT_WEB_PORT,
                "auto_open_browser": True,
                "alert_enabled": True,
                "alert_volume": 0.5,
            },
            "devices": [
                {
                    "id": "dev_001",
                    "name": "Localhost",
                    "ip": "127.0.0.1",
                    "ports": [80, 443],
                    "category": "System",
                    "description": "Local machine",
                    "enabled": True,
                }
            ],
        }

    def _load(self):
        with self._lock:
            if not os.path.exists(self._config_path):
                os.makedirs(self._data_dir, exist_ok=True)
                config = self._default_config()
                self._save_raw(config)
            else:
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)

            self._settings = config.get('settings', self._default_config()['settings'])
            self._devices = [Device.from_dict(d) for d in config.get('devices', [])]

            max_num = 0
            for dev in self._devices:
                if dev.id.startswith('dev_'):
                    try:
                        num = int(dev.id.split('_')[1])
                        max_num = max(max_num, num)
                    except (ValueError, IndexError):
                        pass
            self._next_id = max_num + 1

    def _save_raw(self, config):
        with open(self._config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

    def _save(self):
        config = {
            "version": 1,
            "settings": self._settings,
            "devices": [d.to_dict() for d in self._devices],
        }
        self._save_raw(config)

    def get_devices(self) -> List[Device]:
        with self._lock:
            return list(self._devices)

    def get_enabled_devices(self) -> List[Device]:
        with self._lock:
            return [d for d in self._devices if d.enabled]

    def get_device(self, device_id: str) -> Optional[Device]:
        with self._lock:
            for d in self._devices:
                if d.id == device_id:
                    return d
            return None

    def add_device(self, device: Device) -> Device:
        with self._lock:
            device.id = "dev_{:03d}".format(self._next_id)
            self._next_id += 1
            errors = device.validate()
            if errors:
                raise ValueError("; ".join(errors))
            self._devices.append(device)
            self._save()
            return device

    def update_device(self, device_id: str, data: dict) -> Optional[Device]:
        with self._lock:
            for i, d in enumerate(self._devices):
                if d.id == device_id:
                    for key, val in data.items():
                        if key != 'id' and hasattr(d, key):
                            setattr(d, key, val)
                    errors = d.validate()
                    if errors:
                        raise ValueError("; ".join(errors))
                    self._save()
                    return d
            return None

    def delete_device(self, device_id: str) -> bool:
        with self._lock:
            for i, d in enumerate(self._devices):
                if d.id == device_id:
                    self._devices.pop(i)
                    self._save()
                    return True
            return False

    def get_settings(self) -> dict:
        with self._lock:
            return dict(self._settings)

    def update_settings(self, data: dict) -> dict:
        with self._lock:
            for key, val in data.items():
                if key in self._settings:
                    self._settings[key] = val
            self._save()
            return dict(self._settings)

    def export_config(self) -> dict:
        with self._lock:
            return {
                "version": 1,
                "settings": self._settings,
                "devices": [d.to_dict() for d in self._devices],
            }

    def import_config(self, config: dict):
        with self._lock:
            self._settings = config.get('settings', self._settings)
            self._devices = [Device.from_dict(d) for d in config.get('devices', [])]
            max_num = 0
            for dev in self._devices:
                if dev.id.startswith('dev_'):
                    try:
                        num = int(dev.id.split('_')[1])
                        max_num = max(max_num, num)
                    except (ValueError, IndexError):
                        pass
            self._next_id = max_num + 1
            self._save()
