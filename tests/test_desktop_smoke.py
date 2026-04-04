"""PortDetector Desktop smoke test — offscreen PySide6 윈도우 생성 확인."""

import sys
import os
import pytest

# Path setup
_ROOT = os.path.join(os.path.dirname(__file__), "..")
_SHARED = os.path.join(_ROOT, "..", "..", "_shared")
sys.path.insert(0, _ROOT)
sys.path.insert(0, _SHARED)

os.environ["QT_QPA_PLATFORM"] = "offscreen"


@pytest.fixture(scope="module")
def app():
    from PySide6.QtWidgets import QApplication
    _app = QApplication.instance() or QApplication(sys.argv)
    yield _app


def test_main_window_creates(app, tmp_path):
    """MainWindow가 offscreen에서 정상 생성되는지 확인."""
    from desktop.main_window import MainWindow

    class _LogService:
        def get_all_entries(self, *args, **kwargs):
            return []

        def get_history(self, *args, **kwargs):
            return []

    class _TrafficService:
        def is_available(self):
            return False

        def stop(self):
            return None

    class _ProfileService:
        def list_profiles(self):
            return []

        def save_profile(self, *args, **kwargs):
            return None

        def load_profile(self, *args, **kwargs):
            return {}

        def delete_profile(self, *args, **kwargs):
            return False

    class _BackupService:
        def list_backups(self):
            return []

        def create_backup(self, *args, **kwargs):
            return {"filename": "backup.json"}

        def load_backup(self, *args, **kwargs):
            return {"config": {"settings": {}, "devices": []}}

    class _AlertService:
        def set_sound_enabled(self, *args, **kwargs):
            return None

        def set_escalation_enabled(self, *args, **kwargs):
            return None

        def on_status_update(self, *args, **kwargs):
            return None

        def get_issue_state(self, *args, **kwargs):
            return {}

        def play_alert_sound_async(self, *args, **kwargs):
            return None

    from backend.services.config_service import ConfigService
    from backend.services.uptime_service import UptimeService

    config_service = ConfigService(str(tmp_path))
    log_service = _LogService()
    window = MainWindow(
        config_service,
        log_service,
        _TrafficService(),
        _ProfileService(),
        _AlertService(),
        _BackupService(),
        UptimeService(log_service),
    )
    assert window is not None
    window._stop_workers()
    if hasattr(window, "_tray"):
        window._tray.hide()
    window.close()
    window.deleteLater()


def test_py_compile():
    """desktop/ 하위 모든 .py 파일이 py_compile 통과하는지 확인."""
    import py_compile
    desktop_dir = os.path.join(_ROOT, "desktop")
    errors = []
    for root, _, files in os.walk(desktop_dir):
        for f in files:
            if f.endswith(".py"):
                path = os.path.join(root, f)
                try:
                    py_compile.compile(path, doraise=True)
                except py_compile.PyCompileError as e:
                    errors.append(str(e))
    assert not errors, f"py_compile 실패:\n" + "\n".join(errors)
