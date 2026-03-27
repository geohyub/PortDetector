"""Alert escalation and sound notification service."""

import threading
from collections import defaultdict
from datetime import datetime


class AlertService:
    """Tracks consecutive failures per device and manages alert escalation."""

    # Escalation thresholds: consecutive failures -> severity level
    LEVELS = [
        (1, "warning"),      # 1 failure
        (3, "critical"),     # 3 consecutive
        (10, "emergency"),   # 10 consecutive
    ]

    def __init__(self):
        self._fail_counts = defaultdict(int)  # device_id -> consecutive fail count
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
                self._fail_counts[device_id] = 0
                if prev_count >= 3:
                    return {
                        'escalated': True,
                        'level': 'recovered',
                        'count': 0,
                        'device_id': device_id,
                    }
                return {}

            # Disconnected or delayed
            self._fail_counts[device_id] += 1
            count = self._fail_counts[device_id]

            if not self._escalation_enabled:
                return {}

            # Find current escalation level
            level = None
            for threshold, lvl in reversed(self.LEVELS):
                if count >= threshold:
                    level = lvl
                    break

            # Only alert at exact thresholds to avoid spam
            exact_thresholds = [t for t, _ in self.LEVELS]
            if count in exact_thresholds:
                return {
                    'escalated': True,
                    'level': level,
                    'count': count,
                    'device_id': device_id,
                }

            return {}

    def get_fail_count(self, device_id: str) -> int:
        with self._lock:
            return self._fail_counts.get(device_id, 0)

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
