"""Status change history logging service."""

import json
import os
from datetime import datetime
from typing import List, Optional

from config import MAX_LOG_SIZE_BYTES, MAX_LOG_BACKUPS


class LogService:
    def __init__(self, data_dir: str):
        self._log_path = os.path.join(data_dir, 'history.log')
        os.makedirs(data_dir, exist_ok=True)

    def log_event(self, device_id: str, ip: str, event: str, rtt_ms: Optional[int] = None):
        """Append a status change event."""
        entry = {
            "timestamp": datetime.now().isoformat(timespec='seconds'),
            "device_id": device_id,
            "ip": ip,
            "event": event,
            "rtt_ms": rtt_ms,
        }
        self._rotate_if_needed()
        with open(self._log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    def get_history(self, limit: int = 100, offset: int = 0,
                    device_id: Optional[str] = None) -> List[dict]:
        """Read history entries (newest first)."""
        if not os.path.exists(self._log_path):
            return []

        with open(self._log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        entries = []
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if device_id and entry.get('device_id') != device_id:
                    continue
                entries.append(entry)
            except json.JSONDecodeError:
                continue

        return entries[offset:offset + limit]

    def get_all_entries(self) -> List[dict]:
        """Get all entries for CSV export."""
        if not os.path.exists(self._log_path):
            return []
        with open(self._log_path, 'r', encoding='utf-8') as f:
            entries = []
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return entries

    def _rotate_if_needed(self):
        if not os.path.exists(self._log_path):
            return
        try:
            size = os.path.getsize(self._log_path)
        except OSError:
            return
        if size < MAX_LOG_SIZE_BYTES:
            return

        for i in range(MAX_LOG_BACKUPS, 0, -1):
            src = "{}.{}".format(self._log_path, i) if i > 1 else self._log_path
            dst = "{}.{}".format(self._log_path, i + 1) if i < MAX_LOG_BACKUPS else None
            if dst and os.path.exists(src):
                if os.path.exists(dst):
                    os.remove(dst)
                os.rename(src, dst)
            elif i == MAX_LOG_BACKUPS and os.path.exists(src):
                os.remove(src)

        backup = self._log_path + '.1'
        if os.path.exists(self._log_path):
            os.rename(self._log_path, backup)
