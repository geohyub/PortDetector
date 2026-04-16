"""PortDetector Desktop Application Entry Point."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Path setup


def _resolve_base_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _resolve_bundle_dir() -> str:
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return _resolve_base_dir()


def _resolve_entrypoint() -> str:
    if getattr(sys, "frozen", False):
        return sys.executable
    return os.path.abspath(__file__)


BASE_DIR = _resolve_base_dir()
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
BUNDLE_DIR = _resolve_bundle_dir()
if not getattr(sys, "frozen", False):
    _shared = Path(BASE_DIR).resolve().parents[2] / "_shared"
    if str(_shared) not in sys.path:
        sys.path.insert(0, str(_shared))

DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

from config import APP_NAME, VERSION

SINGLE_INSTANCE_KEY = "PortDetector_SingleInstance_v2"
_ACTIVATE_MSG = b"ACTIVATE"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=f"{APP_NAME} desktop startup")
    parser.add_argument(
        "--doctor",
        action="store_true",
        help="Run a local-only preflight check and exit.",
    )
    parser.add_argument(
        "--doctor-export",
        metavar="PATH",
        help="Write the doctor operator packet to PATH as JSON and exit.",
    )
    return parser


def build_runtime_context() -> dict[str, object]:
    return {
        "mode": "packaged" if getattr(sys, "frozen", False) else "source",
        "is_frozen": bool(getattr(sys, "frozen", False)),
        "base_dir": _resolve_base_dir(),
        "bundle_dir": _resolve_bundle_dir(),
        "entrypoint": _resolve_entrypoint(),
    }


def run_doctor(export_path: str | None = None) -> int:
    from backend.services.doctor_service import (
        export_operator_packet,
        print_preflight,
        run_preflight,
    )

    report = run_preflight(DATA_DIR, "desktop", runtime_context=build_runtime_context())
    if export_path:
        saved_path = export_operator_packet(report, export_path)
        print(f"Operator packet written to {saved_path}")
    return print_preflight(report)


def _try_activate_existing() -> bool:
    """Try to send an activation message to an already-running instance.

    Returns True if another instance responded (caller should exit).
    Returns False if no instance is listening (caller should proceed).
    """
    from PySide6.QtNetwork import QLocalSocket

    sock = QLocalSocket()
    sock.connectToServer(SINGLE_INSTANCE_KEY)
    if sock.waitForConnected(500):
        sock.write(_ACTIVATE_MSG)
        sock.waitForBytesWritten(500)
        sock.disconnectFromServer()
        return True
    return False


def run_desktop_app() -> int:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    from PySide6.QtNetwork import QLocalServer
    from geoview_pyside6.runtime import run_with_crash_dialog

    from backend.services.config_service import ConfigService
    from backend.services.log_service import LogService
    from backend.services.traffic_service import TrafficService
    from backend.services.profile_service import ProfileService
    from backend.services.alert_service import AlertService
    from backend.services.backup_service import BackupService
    from backend.services.uptime_service import UptimeService
    from desktop.main_window import MainWindow
    from desktop.i18n import set_language

    def _launch() -> int:
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )

        app = QApplication.instance() or QApplication(sys.argv)
        app.setApplicationName(APP_NAME)
        app.setApplicationVersion(VERSION)

        if _try_activate_existing():
            return 0

        QLocalServer.removeServer(SINGLE_INSTANCE_KEY)

        server = QLocalServer()
        if not server.listen(SINGLE_INSTANCE_KEY):
            return 0

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

        try:
            settings = config_service.get_settings()
            lang = settings.get('language', 'ko')
            set_language(lang)

            window = MainWindow(
                config_service, log_service, traffic_service,
                profile_service, alert_service, backup_service, uptime_service,
            )
            window.show()

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
            return app.exec()
        finally:
            server.close()
            traffic_service.stop()

    return run_with_crash_dialog(APP_NAME, _launch)


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    if args.doctor:
        return run_doctor(args.doctor_export)
    return run_desktop_app()


if __name__ == '__main__':
    raise SystemExit(main())
