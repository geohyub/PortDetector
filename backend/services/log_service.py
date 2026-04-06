"""Status change history logging service."""

import json
import os
import threading
from datetime import datetime
from contextlib import contextmanager
from typing import List, Optional

from config import MAX_LOG_SIZE_BYTES, MAX_LOG_BACKUPS

try:
    import msvcrt
except ImportError:  # pragma: no cover - non-Windows platforms
    msvcrt = None

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows platforms
    fcntl = None

_SENSITIVE_KEY_PATTERNS = (
    "password",
    "passwd",
    "passphrase",
    "secret",
    "token",
    "api_key",
    "apikey",
    "auth",
    "authorization",
    "cookie",
    "session",
    "credential",
    "private_key",
)
_MAX_TEXT_LENGTH = 512
_PATH_LOCKS = {}
_PATH_LOCKS_GUARD = threading.Lock()


def _get_path_lock(path: str) -> threading.Lock:
    with _PATH_LOCKS_GUARD:
        lock = _PATH_LOCKS.get(path)
        if lock is None:
            lock = threading.Lock()
            _PATH_LOCKS[path] = lock
        return lock


class LogService:
    def __init__(self, data_dir: str):
        self._log_path = os.path.join(data_dir, 'history.log')
        self._lock_path = self._log_path + '.lock'
        self._write_lock = _get_path_lock(self._log_path)
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
                entry[key] = self._sanitize_value(key, value)
        with self._acquire_log_lock():
            self._rotate_if_needed()
            with open(self._log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    def _read_log_snapshot(self) -> bytes:
        """Read a consistent snapshot of the current log file."""
        if not os.path.exists(self._log_path):
            return b""

        with self._acquire_log_lock():
            try:
                with open(self._log_path, 'rb') as f:
                    return f.read()
            except OSError:
                return b""

    def _sanitize_value(self, key: str, value):
        key_hint = (key or "").strip().lower().replace("-", "_")
        if any(pattern in key_hint for pattern in _SENSITIVE_KEY_PATTERNS):
            return "[REDACTED]"

        if isinstance(value, dict):
            return {
                str(child_key): self._sanitize_value(str(child_key), child_value)
                for child_key, child_value in value.items()
                if child_value is not None
            }
        if isinstance(value, list):
            return [self._sanitize_value("", item) for item in value]
        if isinstance(value, tuple):
            return tuple(self._sanitize_value("", item) for item in value)
        if isinstance(value, str) and len(value) > _MAX_TEXT_LENGTH:
            return value[:_MAX_TEXT_LENGTH] + "…"

        try:
            json.dumps(value, ensure_ascii=False)
            return value
        except (TypeError, ValueError):
            return str(value)

    def get_history(self, limit: int = 100, offset: int = 0,
                    device_id: Optional[str] = None,
                    events: Optional[List[str]] = None) -> List[dict]:
        """Read history entries (newest first). Uses reverse file reading for efficiency."""
        snapshot = self._read_log_snapshot()
        if not snapshot:
            return []

        # Read file in reverse to avoid loading entire file for paginated queries
        entries = []
        target = offset + limit
        skipped = 0

        buf = b''
        remaining = len(snapshot)
        while remaining > 0 and len(entries) < target:
            chunk_size = min(8192, remaining)
            remaining -= chunk_size
            buf = snapshot[remaining:remaining + chunk_size] + buf
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
                        skipped += 1
                    else:
                        entries.append(entry)
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass

        return entries

    def get_all_entries(self, device_id: Optional[str] = None,
                        events: Optional[List[str]] = None) -> List[dict]:
        """Get all entries for CSV export."""
        snapshot = self._read_log_snapshot()
        if not snapshot:
            return []

        entries = []
        for line in snapshot.decode('utf-8', errors='ignore').splitlines():
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

    @contextmanager
    def _acquire_log_lock(self):
        with self._write_lock:
            lock_fd = os.open(self._lock_path, os.O_CREAT | os.O_RDWR)
            try:
                if msvcrt is not None:
                    os.lseek(lock_fd, 0, os.SEEK_SET)
                    msvcrt.locking(lock_fd, msvcrt.LK_LOCK, 1)
                elif fcntl is not None:
                    fcntl.flock(lock_fd, fcntl.LOCK_EX)
                yield
            finally:
                try:
                    if msvcrt is not None:
                        os.lseek(lock_fd, 0, os.SEEK_SET)
                        msvcrt.locking(lock_fd, msvcrt.LK_UNLCK, 1)
                    elif fcntl is not None:
                        fcntl.flock(lock_fd, fcntl.LOCK_UN)
                finally:
                    os.close(lock_fd)

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
            os.replace(self._log_path, backup)
