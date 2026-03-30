"""PortDetector — PySide6 Desktop Application Entry Point."""

import os
import sys

# Path setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtNetwork import QLocalServer, QLocalSocket

from config import APP_NAME, VERSION
from backend.services.config_service import ConfigService
from backend.services.log_service import LogService
from backend.services.traffic_service import TrafficService
from backend.services.profile_service import ProfileService
from backend.services.alert_service import AlertService
from backend.services.backup_service import BackupService
from backend.services.uptime_service import UptimeService
from desktop.main_window import MainWindow
from desktop.i18n import set_language

SINGLE_INSTANCE_KEY = "PortDetector_SingleInstance_v2"
_ACTIVATE_MSG = b"ACTIVATE"


def _try_activate_existing() -> bool:
    """Try to send an activation message to an already-running instance.

    Returns True if another instance responded (caller should exit).
    Returns False if no instance is listening (caller should proceed).
    """
    sock = QLocalSocket()
    sock.connectToServer(SINGLE_INSTANCE_KEY)
    if sock.waitForConnected(500):
        sock.write(_ACTIVATE_MSG)
        sock.waitForBytesWritten(500)
        sock.disconnectFromServer()
        return True
    return False


def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(VERSION)

    # ── Single instance guard ──
    if _try_activate_existing():
        # Another instance is already running — it will bring itself forward.
        sys.exit(0)

    # Remove stale socket left by a crash (Linux/macOS) or unclean exit
    QLocalServer.removeServer(SINGLE_INSTANCE_KEY)

    server = QLocalServer()
    if not server.listen(SINGLE_INSTANCE_KEY):
        # Extremely unlikely: another instance raced us. Exit gracefully.
        sys.exit(0)

    # Services
    config_service = ConfigService(DATA_DIR)
    log_service = LogService(DATA_DIR)
    profile_service = ProfileService(DATA_DIR)
    alert_service = AlertService()
    backup_service = BackupService(DATA_DIR)
    uptime_service = UptimeService(log_service)

    traffic_service = TrafficService()
    traffic_service.start()
    if traffic_service.is_available():
        print("Traffic capture: ACTIVE (admin privileges detected)")
    else:
        print("Traffic capture: DISABLED (run as administrator to enable)")

    # ── Language setup from saved settings ──
    settings = config_service.get_settings()
    lang = settings.get('language', 'ko')
    set_language(lang)

    # Main window
    window = MainWindow(
        config_service, log_service, traffic_service,
        profile_service, alert_service, backup_service, uptime_service,
    )
    window.show()

    # ── Listen for activation requests from new instances ──
    def _on_new_connection():
        conn = server.nextPendingConnection()
        if conn:
            conn.waitForReadyRead(500)
            data = conn.readAll().data()
            conn.close()
            if data == _ACTIVATE_MSG:
                window.showNormal()
                window.raise_()
                window.activateWindow()

    server.newConnection.connect(_on_new_connection)

    print(f"{APP_NAME} v{VERSION} started (PySide6 Desktop)")

    ret = app.exec()

    # Cleanup
    server.close()
    traffic_service.stop()
    sys.exit(ret)


if __name__ == '__main__':
    main()
