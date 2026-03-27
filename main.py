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

from config import APP_NAME, VERSION
from backend.services.config_service import ConfigService
from backend.services.log_service import LogService
from backend.services.traffic_service import TrafficService
from backend.services.profile_service import ProfileService
from backend.services.alert_service import AlertService
from backend.services.uptime_service import UptimeService
from desktop.main_window import MainWindow


def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(VERSION)

    # Services
    config_service = ConfigService(DATA_DIR)
    log_service = LogService(DATA_DIR)
    profile_service = ProfileService(DATA_DIR)
    alert_service = AlertService()
    uptime_service = UptimeService(log_service)

    traffic_service = TrafficService()
    traffic_service.start()
    if traffic_service.is_available():
        print("Traffic capture: ACTIVE (admin privileges detected)")
    else:
        print("Traffic capture: DISABLED (run as administrator to enable)")

    # Main window
    window = MainWindow(
        config_service, log_service, traffic_service,
        profile_service, alert_service, uptime_service,
    )
    window.show()

    print(f"{APP_NAME} v{VERSION} started (PySide6 Desktop)")

    ret = app.exec()

    # Cleanup
    traffic_service.stop()
    sys.exit(ret)


if __name__ == '__main__':
    main()
