"""Alert escalation and sound notification service."""

import threading
from collections import defaultdict


class AlertService:
    """Tracks consecutive failures per device and manages alert escalation."""

    LEVELS = {
        "disconnected": [
            (1, "warning"),
            (3, "critical"),
            (10, "emergency"),
        ],
        "delayed": [
            (3, "warning"),
            (6, "critical"),
        ],
    }

    def __init__(self):
        self._fail_counts = defaultdict(int)
        self._issue_status = {}
        self._lock = threading.Lock()
        self._sound_enabled = True
        self._escalation_enabled = True

    def on_status_update(self, device_id: str, status: str) -> dict:
        """Process a status update. Returns alert info if escalation triggered.

        Returns dict with keys: escalated, level, count, device_id
        or empty dict if no escalation.
        """
        with self._lock:
            if status == "connected":
                prev_count = self._fail_counts.get(device_id, 0)
                prev_issue = self._issue_status.get(device_id)
                self._fail_counts[device_id] = 0
                self._issue_status[device_id] = None
                recovery_threshold = 1 if prev_issue == "disconnected" else 3
                if prev_issue and prev_count >= recovery_threshold:
                    return {
                        'escalated': True,
                        'level': 'recovered',
                        'count': 0,
                        'device_id': device_id,
                        'issue_status': prev_issue,
                    }
                return {}

            prev_issue = self._issue_status.get(device_id)
            if prev_issue == status:
                self._fail_counts[device_id] += 1
            elif prev_issue == "delayed" and status == "disconnected":
                self._fail_counts[device_id] += 1
            else:
                self._fail_counts[device_id] = 1

            self._issue_status[device_id] = status
            count = self._fail_counts[device_id]

            if not self._escalation_enabled:
                return {}

            levels = self.LEVELS.get(status, [])
            level = None
            for threshold, lvl in reversed(levels):
                if count >= threshold:
                    level = lvl
                    break

            exact_thresholds = [t for t, _ in levels]
            if count in exact_thresholds:
                return {
                    'escalated': True,
                    'level': level,
                    'count': count,
                    'device_id': device_id,
                    'issue_status': status,
                }

            return {}

    def get_fail_count(self, device_id: str) -> int:
        with self._lock:
            return self._fail_counts.get(device_id, 0)

    def get_issue_status(self, device_id: str) -> str | None:
        with self._lock:
            return self._issue_status.get(device_id)

    def get_issue_state(self, device_id: str) -> dict:
        with self._lock:
            return {
                'count': self._fail_counts.get(device_id, 0),
                'issue_status': self._issue_status.get(device_id),
            }

    def set_sound_enabled(self, enabled: bool):
        self._sound_enabled = enabled

    def set_escalation_enabled(self, enabled: bool):
        self._escalation_enabled = enabled

    @property
    def sound_enabled(self):
        return self._sound_enabled

    def play_alert_sound(self, level: str = "warning"):
        """Play alert sound based on severity level."""
        if not self._sound_enabled:
            return
        try:
            import winsound
            if level == "emergency":
                # Three rapid beeps
                for _ in range(3):
                    winsound.Beep(1000, 200)
            elif level == "critical":
                # Two beeps
                winsound.Beep(800, 300)
                winsound.Beep(800, 300)
            elif level == "warning":
                winsound.Beep(600, 400)
            elif level == "advisory":
                winsound.Beep(520, 180)
            elif level == "recovered":
                # Pleasant ascending tone
                winsound.Beep(400, 150)
                winsound.Beep(600, 150)
        except Exception:
            pass  # Not on Windows or winsound not available

    def play_alert_sound_async(self, level: str = "warning"):
        """Play sound without blocking."""
        t = threading.Thread(target=self.play_alert_sound, args=(level,), daemon=True)
        t.start()
