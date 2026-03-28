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

    def log_event(self, device_id: str, ip: str, event: str, rtt_ms: Optional[int] = None, **extra):
        """Append a status change event."""
        entry = {
            "timestamp": datetime.now().isoformat(timespec='seconds'),
            "device_id": device_id,
            "ip": ip,
            "event": event,
            "rtt_ms": rtt_ms,
        }
        for key, value in extra.items():
            if value is not None:
                entry[key] = value
        self._rotate_if_needed()
        with open(self._log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    def get_history(self, limit: int = 100, offset: int = 0,
                    device_id: Optional[str] = None,
                    events: Optional[List[str]] = None) -> List[dict]:
        """Read history entries (newest first). Uses reverse file reading for efficiency."""
        if not os.path.exists(self._log_path):
            return []

        # Read file in reverse to avoid loading entire file for paginated queries
        entries = []
        target = offset + limit
        skipped = 0

        try:
            with open(self._log_path, 'rb') as f:
                f.seek(0, 2)
                remaining = f.tell()
                buf = b''
                while remaining > 0 and len(entries) < target:
                    chunk_size = min(8192, remaining)
                    remaining -= chunk_size
                    f.seek(remaining)
                    buf = f.read(chunk_size) + buf
                    lines = buf.split(b'\n')
                    buf = lines[0]  # partial line carried over
                    for line in reversed(lines[1:]):
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            entry = json.loads(line.decode('utf-8'))
                            if device_id and entry.get('device_id') != device_id:
                                continue
                            if events and entry.get('event') not in events:
                                continue
                            if skipped < offset:
                                skipped += 1
                                continue
                            entries.append(entry)
                            if len(entries) >= limit:
                                break
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            continue

                # Process remaining buffer
                if buf.strip() and len(entries) < limit:
                    try:
                        entry = json.loads(buf.strip().decode('utf-8'))
                        ok = not device_id or entry.get('device_id') == device_id
                        if ok and events:
                            ok = entry.get('event') in events
                        if ok:
                            if skipped < offset:
                                pass
                            else:
                                entries.append(entry)
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        pass
        except OSError:
            return []

        return entries

    def get_all_entries(self, device_id: Optional[str] = None,
                        events: Optional[List[str]] = None) -> List[dict]:
        """Get all entries for CSV export."""
        if not os.path.exists(self._log_path):
            return []
        with open(self._log_path, 'r', encoding='utf-8') as f:
            entries = []
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entry = json.loads(line)
                        if device_id and entry.get('device_id') != device_id:
                            continue
                        if events and entry.get('event') not in events:
                            continue
                        entries.append(entry)
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
