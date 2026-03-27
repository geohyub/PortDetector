"""Profile management — save/load/switch device sets per vessel/project."""

import json
import os
import shutil
from datetime import datetime
from typing import List, Optional


class ProfileService:
    def __init__(self, data_dir: str):
        self._profiles_dir = os.path.join(data_dir, 'profiles')
        os.makedirs(self._profiles_dir, exist_ok=True)
        self._active_profile = None  # None = default (devices.json)

    def list_profiles(self) -> List[dict]:
        """List all saved profiles with metadata."""
        profiles = []
        for fname in sorted(os.listdir(self._profiles_dir)):
            if not fname.endswith('.json'):
                continue
            path = os.path.join(self._profiles_dir, fname)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                profiles.append({
                    'name': data.get('name', fname.replace('.json', '')),
                    'filename': fname,
                    'vessel': data.get('vessel', ''),
                    'device_count': len(data.get('devices', [])),
                    'created': data.get('created', ''),
                    'description': data.get('description', ''),
                })
            except (json.JSONDecodeError, OSError):
                continue
        return profiles

    def save_profile(self, name: str, devices: list, settings: dict,
                     vessel: str = '', description: str = '') -> str:
        """Save current device config as a named profile."""
        safe_name = "".join(c for c in name if c.isalnum() or c in '-_ ').strip()
        filename = f"{safe_name}.json"
        path = os.path.join(self._profiles_dir, filename)

        profile = {
            'name': name,
            'vessel': vessel,
            'description': description,
            'created': datetime.now().isoformat(timespec='seconds'),
            'settings': settings,
            'devices': devices,
        }

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)

        return filename

    def load_profile(self, filename: str) -> Optional[dict]:
        """Load a profile's devices and settings."""
        path = os.path.join(self._profiles_dir, filename)
        if not os.path.exists(path):
            return None
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def delete_profile(self, filename: str) -> bool:
        path = os.path.join(self._profiles_dir, filename)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    def get_active_profile(self) -> Optional[str]:
        return self._active_profile

    def set_active_profile(self, filename: Optional[str]):
        self._active_profile = filename
