"""Background ping monitoring worker."""

import threading
from collections import deque
from datetime import datetime

from backend.services.ping_service import ping
from backend.models.status import PingResult

MAX_HISTORY_PER_DEVICE = 120  # ~10 minutes at 5s interval


class PingWorker:
    def __init__(self, config_service, log_service, socketio, delay_threshold_ms=200):
        self._config_service = config_service
        self._log_service = log_service
        self._socketio = socketio
        self._delay_threshold = delay_threshold_ms
        self._stop_event = threading.Event()
        self._thread = None
        self._interval = 5
        self._prev_status = {}  # device_id -> status
        self._current_status = {}  # device_id -> {status, rtt_ms, timestamp}
        self._rtt_history = {}  # device_id -> deque of {rtt_ms, timestamp}

    def start(self, interval: int = 5):
        self._interval = interval
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)

    def update_interval(self, interval: int):
        self._interval = interval

    def update_threshold(self, threshold_ms: int):
        self._delay_threshold = threshold_ms

    def get_rtt_history(self):
        """Get RTT history for all devices (for graphs)."""
        result = {}
        for dev_id, history in self._rtt_history.items():
            result[dev_id] = list(history)
        return result

    def get_current_status(self):
        """Get current status of all monitored devices."""
        return dict(self._current_status)

    def _run(self):
        while not self._stop_event.is_set():
            devices = self._config_service.get_enabled_devices()
            results = []

            for device in devices:
                if self._stop_event.is_set():
                    break

                success, rtt_ms = ping(device.ip)

                if not success:
                    status = "disconnected"
                elif rtt_ms is not None and rtt_ms > self._delay_threshold:
                    status = "delayed"
                else:
                    status = "connected"

                now = datetime.now().isoformat(timespec='seconds')

                result = PingResult(
                    device_id=device.id,
                    ip=device.ip,
                    status=status,
                    rtt_ms=rtt_ms,
                    timestamp=now,
                )
                results.append(result.to_dict())

                # Store current status
                self._current_status[device.id] = {
                    'status': status, 'rtt_ms': rtt_ms, 'timestamp': now,
                }

                # Store RTT history for graphs
                if device.id not in self._rtt_history:
                    self._rtt_history[device.id] = deque(maxlen=MAX_HISTORY_PER_DEVICE)
                self._rtt_history[device.id].append({
                    'rtt_ms': rtt_ms, 'timestamp': now,
                })

                # Log status changes
                prev = self._prev_status.get(device.id)
                if prev != status:
                    self._prev_status[device.id] = status
                    if prev is not None:
                        # Best-effort history/notification side effects must not
                        # stop the monitoring loop if local storage or SocketIO
                        # is temporarily unavailable.
                        try:
                            self._log_service.log_event(
                                device.id, device.ip, status, rtt_ms
                            )
                        except Exception:
                            pass
                        try:
                            self._socketio.emit('status_change', {
                                'device_id': device.id,
                                'ip': device.ip,
                                'name': device.name,
                                'old_status': prev,
                                'new_status': status,
                                'timestamp': now,
                            })
                        except Exception:
                            pass

            if results:
                self._socketio.emit('batch_ping_update', results)

            self._stop_event.wait(self._interval)
