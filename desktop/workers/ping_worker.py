"""Qt-based ping monitoring worker — replaces SocketIO PingWorker."""

import threading
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from PySide6.QtCore import QObject, QThread, Signal

from backend.services.ping_service import ping
from backend.models.status import PingResult
from backend.utils.monitoring_presenter import build_status_reason

MAX_HISTORY_PER_DEVICE = 120
MAX_PING_WORKERS = 10


class PingWorkerSignals(QObject):
    batch_update = Signal(list)        # list of PingResult dicts
    status_change = Signal(dict)       # {device_id, ip, name, old_status, new_status, timestamp}


class PingWorkerThread(QThread):
    """Runs one ping cycle for all devices in parallel, then sleeps."""

    def __init__(self, config_service, log_service, delay_threshold_ms=200):
        super().__init__()
        self.signals = PingWorkerSignals()
        self._config_service = config_service
        self._log_service = log_service
        self._delay_threshold = delay_threshold_ms
        self._interval = 5
        self._running = True

        self._prev_status = {}
        self._current_status = {}
        self._rtt_history = {}
        self._history_lock = threading.Lock()

    def set_interval(self, interval: int):
        self._interval = interval

    def set_threshold(self, threshold_ms: int):
        self._delay_threshold = threshold_ms

    def get_rtt_history(self):
        with self._history_lock:
            result = {}
            for dev_id, history in self._rtt_history.items():
                result[dev_id] = list(history)
            return result

    def get_current_status(self):
        return dict(self._current_status)

    def stop(self):
        self._running = False

    def _ping_device(self, device):
        """Ping a single device — runs inside ThreadPoolExecutor."""
        success, rtt_ms = ping(device.ip)
        return device, success, rtt_ms

    def run(self):
        while self._running:
            devices = self._config_service.get_enabled_devices()
            results = []
            now = datetime.now().isoformat(timespec='seconds')

            # Parallel ping — up to 10 concurrent subprocess pings
            workers = min(MAX_PING_WORKERS, len(devices)) if devices else 1
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = {
                    executor.submit(self._ping_device, dev): dev
                    for dev in devices
                }
                for future in as_completed(futures):
                    if not self._running:
                        break
                    try:
                        device, success, rtt_ms = future.result()
                    except Exception:
                        continue

                    if not success:
                        status = "disconnected"
                    elif rtt_ms is not None and rtt_ms > self._delay_threshold:
                        status = "delayed"
                    else:
                        status = "connected"

                    result = PingResult(
                        device_id=device.id,
                        ip=device.ip,
                        status=status,
                        rtt_ms=rtt_ms,
                        timestamp=now,
                    )
                    results.append(result.to_dict())

                    self._current_status[device.id] = {
                        'status': status, 'rtt_ms': rtt_ms, 'timestamp': now,
                    }

                    with self._history_lock:
                        if device.id not in self._rtt_history:
                            self._rtt_history[device.id] = deque(maxlen=MAX_HISTORY_PER_DEVICE)
                        self._rtt_history[device.id].append({
                            'rtt_ms': rtt_ms, 'timestamp': now,
                        })

                    prev = self._prev_status.get(device.id)
                    if prev != status:
                        self._prev_status[device.id] = status
                        if prev is not None:
                            try:
                                self._log_service.log_event(
                                    device.id,
                                    device.ip,
                                    status,
                                    rtt_ms,
                                    device_name=device.name,
                                    category=device.category,
                                    importance=getattr(device, 'importance', 'standard'),
                                    description=device.description,
                                    ports=list(device.ports),
                                    old_status=prev,
                                    reason=build_status_reason(status, rtt_ms, self._delay_threshold),
                                )
                            except Exception:
                                # Keep monitoring even if the history sink is unavailable.
                                pass
                            try:
                                self.signals.status_change.emit({
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
                self.signals.batch_update.emit(results)

            # Sleep in small increments so stop() is responsive
            for _ in range(self._interval * 10):
                if not self._running:
                    break
                self.msleep(100)
