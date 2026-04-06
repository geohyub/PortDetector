"""Configuration backup service for safe replace/restore flows."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import List, Optional

from config import MAX_CONFIG_BACKUPS


class BackupService:
    def __init__(self, data_dir: str):
        self._backups_dir = os.path.join(data_dir, "backups")
        os.makedirs(self._backups_dir, exist_ok=True)

    def _safe_slug(self, value: str) -> str:
        slug = re.sub(r"[^A-Za-z0-9_-]+", "-", value or "backup").strip("-").lower()
        return slug or "backup"

    def create_backup(self, config: dict, source: str, note: str = "") -> dict:
        created = datetime.now().isoformat(timespec="seconds")
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{stamp}_{self._safe_slug(source)}.json"
        path = os.path.join(self._backups_dir, filename)

        payload = {
            "created": created,
            "source": source,
            "note": note,
            "device_count": len(config.get("devices", [])),
            "config": config,
        }

        tmp_path = None
        try:
            with NamedTemporaryFile("w", delete=False, dir=self._backups_dir, encoding="utf-8") as tmp:
                tmp_path = tmp.name
                json.dump(payload, tmp, indent=2, ensure_ascii=False)
                tmp.flush()
                os.fsync(tmp.fileno())
            os.replace(tmp_path, path)
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

        self._prune_backups()

        return {
            "filename": filename,
            "path": path,
            "created": created,
            "source": source,
            "note": note,
            "device_count": payload["device_count"],
        }

    def list_backups(self) -> List[dict]:
        results = []
        for path in self._sorted_backup_paths():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    payload = json.load(f)
                results.append({
                    "filename": os.path.basename(path),
                    "created": payload.get("created", ""),
                    "source": payload.get("source", ""),
                    "note": payload.get("note", ""),
                    "device_count": payload.get("device_count", len(payload.get("config", {}).get("devices", []))),
                    "path": path,
                })
            except (OSError, json.JSONDecodeError):
                continue
        return results

    def load_backup(self, filename: str) -> Optional[dict]:
        safe_name = os.path.basename(filename or "")
        if not safe_name or safe_name != filename:
            return None

        path = Path(self._backups_dir) / safe_name
        try:
            if Path(self._backups_dir).resolve() not in path.resolve().parents and path.resolve() != Path(self._backups_dir).resolve():
                return None
        except OSError:
            return None

        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def restore_backup(self, filename: str) -> Optional[dict]:
        """Load a backup and return a validated restore payload."""
        payload = self.load_backup(filename)
        if not isinstance(payload, dict):
            return None

        config = payload.get("config")
        if not isinstance(config, dict):
            return None

        restored = dict(payload)
        restored["filename"] = os.path.basename(filename or "")
        device_count = restored.get("device_count")
        if not isinstance(device_count, int) or device_count < 0:
            device_count = len(config.get("devices", []))
        restored["device_count"] = device_count
        restored["config"] = config
        return restored

    def _sorted_backup_paths(self) -> List[str]:
        paths = []
        for fname in os.listdir(self._backups_dir):
            if not fname.endswith(".json"):
                continue
            path = os.path.join(self._backups_dir, fname)
            if os.path.isfile(path):
                paths.append(path)
        paths.sort(key=lambda p: (os.path.getmtime(p), os.path.basename(p)), reverse=True)
        return paths

    def _prune_backups(self, keep_latest: Optional[int] = None):
        if keep_latest is None:
            keep_latest = MAX_CONFIG_BACKUPS
        if keep_latest < 1:
            return

        paths = self._sorted_backup_paths()
        for path in paths[keep_latest:]:
            try:
                os.remove(path)
            except OSError:
                continue
