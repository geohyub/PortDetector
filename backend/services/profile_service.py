"""Profile management — save/load/switch device sets per vessel/project."""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import List, Optional

from backend.services.import_validation import validate_profile_payload


class ProfileService:
    def __init__(self, data_dir: str):
        self._profiles_dir = os.path.join(data_dir, 'profiles')
        os.makedirs(self._profiles_dir, exist_ok=True)
        self._active_profile = None  # None = default (devices.json)

    def _safe_profile_name(self, name: str) -> str:
        safe_name = "".join(c for c in (name or "") if c.isalnum() or c in '-_ ').strip()
        return safe_name or "profile"

    def _resolve_profile_path(self, filename: str) -> Optional[Path]:
        safe_name = os.path.basename(filename or "")
        if not safe_name or safe_name != filename:
            return None

        path = Path(self._profiles_dir) / safe_name
        try:
            profiles_dir = Path(self._profiles_dir).resolve()
            resolved = path.resolve()
            if profiles_dir not in resolved.parents and resolved != profiles_dir:
                return None
        except OSError:
            return None
        return path

    def list_profiles(self) -> List[dict]:
        """List all saved profiles with metadata."""
        profiles = []
        for fname in sorted(os.listdir(self._profiles_dir)):
            if not fname.endswith('.json'):
                continue
            path = os.path.join(self._profiles_dir, fname)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = validate_profile_payload(json.load(f))
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
        safe_name = self._safe_profile_name(name)
        filename = f"{safe_name}.json"
        path = Path(self._profiles_dir) / filename

        profile = {
            'name': name,
            'vessel': vessel,
            'description': description,
            'created': datetime.now().isoformat(timespec='seconds'),
            'settings': settings,
            'devices': devices,
        }

        tmp_path = None
        try:
            with NamedTemporaryFile('w', delete=False, dir=self._profiles_dir, encoding='utf-8') as tmp:
                tmp_path = tmp.name
                json.dump(profile, tmp, indent=2, ensure_ascii=False)
                tmp.flush()
                os.fsync(tmp.fileno())
            os.replace(tmp_path, path)
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

        return filename

    def load_profile(self, filename: str) -> Optional[dict]:
        """Load a profile's devices and settings."""
        path = self._resolve_profile_path(filename)
        if path is None or not path.exists():
            return None
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return validate_profile_payload(json.load(f))
        except (json.JSONDecodeError, OSError, ValueError):
            return None

    def delete_profile(self, filename: str) -> bool:
        path = self._resolve_profile_path(filename)
        if path is not None and path.exists():
            os.remove(path)
            return True
        return False

    def get_active_profile(self) -> Optional[str]:
        return self._active_profile

    def set_active_profile(self, filename: Optional[str]):
        self._active_profile = filename
