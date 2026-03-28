"""Configuration backup service for safe replace/restore flows."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from typing import List, Optional


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

        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

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
        for fname in sorted(os.listdir(self._backups_dir), reverse=True):
            if not fname.endswith(".json"):
                continue
            path = os.path.join(self._backups_dir, fname)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    payload = json.load(f)
                results.append({
                    "filename": fname,
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
        path = os.path.join(self._backups_dir, filename)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
