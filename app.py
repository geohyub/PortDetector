"""PortDetector - Ship Network Monitoring Tool."""

import atexit
import os
import sys
import threading
import webbrowser

from flask import Flask, render_template
from flask_socketio import SocketIO

from config import APP_NAME, VERSION, DEFAULT_WEB_PORT

# Path resolution for PyInstaller
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
    BUNDLE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    BUNDLE_DIR = BASE_DIR

DATA_DIR = os.path.join(BASE_DIR, 'data')
TEMPLATE_DIR = os.path.join(BUNDLE_DIR, 'frontend', 'templates')
STATIC_DIR = os.path.join(BUNDLE_DIR, 'frontend', 'static')

# Flask app
app = Flask(
    __name__,
    template_folder=TEMPLATE_DIR,
    static_folder=STATIC_DIR,
)
app.config['SECRET_KEY'] = 'portdetector-local-only'

socketio = SocketIO(app, async_mode='threading', cors_allowed_origins='*')

# Services
from backend.services.config_service import ConfigService
from backend.services.log_service import LogService

config_service = ConfigService(DATA_DIR)
log_service = LogService(DATA_DIR)

# Workers
from backend.workers.ping_worker import PingWorker
from backend.workers.scan_worker import ScanWorker
from backend.workers.interface_worker import InterfaceWorker
from backend.workers.scheduler import Scheduler

settings = config_service.get_settings()

ping_worker = PingWorker(
    config_service, log_service, socketio,
    delay_threshold_ms=settings.get('delay_threshold_ms', 200),
)
scan_worker = ScanWorker(socketio)
interface_worker = InterfaceWorker(socketio)

# Traffic capture (requires admin privileges)
from backend.services.traffic_service import TrafficService
traffic_service = TrafficService()

scheduler = Scheduler(ping_worker, scan_worker, interface_worker)

# Routes
from backend.routes import api, init_routes

init_routes(config_service, log_service, scan_worker, interface_worker, ping_worker, socketio, traffic_service)
app.register_blueprint(api)

# SocketIO events
from backend.socketio_events import register_socketio_events

register_socketio_events(socketio, scan_worker, scheduler)


@app.route('/')
def index():
    return render_template('index.html', version=VERSION)


def start_tray_icon(port):
    """Start system tray icon in a separate thread."""
    try:
        from pystray import Icon, Menu, MenuItem
        from PIL import Image

        icon_path = os.path.join(BUNDLE_DIR, 'assets', 'icon.ico')
        if os.path.exists(icon_path):
            image = Image.open(icon_path)
        else:
            # Create a simple colored icon if .ico not found
            image = Image.new('RGB', (64, 64), color=(0, 180, 216))

        def open_browser(icon, item):
            webbrowser.open("http://127.0.0.1:{}".format(port))

        def quit_app(icon, item):
            icon.stop()
            scheduler.stop_all()
            os._exit(0)

        menu = Menu(
            MenuItem("{} v{}".format(APP_NAME, VERSION), None, enabled=False),
            Menu.SEPARATOR,
            MenuItem("Open Browser", open_browser, default=True),
            MenuItem("Exit", quit_app),
        )

        icon = Icon(APP_NAME, image, "{} - Running".format(APP_NAME), menu)
        icon.run()
    except ImportError:
        pass  # pystray not available, skip tray icon


def cleanup():
    scheduler.stop_all()
    traffic_service.stop()


atexit.register(cleanup)

if __name__ == '__main__':
    port = settings.get('web_port', DEFAULT_WEB_PORT)

    # Start traffic capture (admin only, graceful fallback)
    traffic_service.start()
    if traffic_service.is_available():
        print("Traffic capture: ACTIVE (admin privileges detected)")
    else:
        print("Traffic capture: DISABLED (run as administrator to enable per-device traffic)")

    # Start workers
    scheduler.start_all(
        ping_interval=settings.get('ping_interval_seconds', 5),
        interface_interval=settings.get('interface_poll_seconds', 3),
    )

    # Start tray icon
    tray_thread = threading.Thread(target=start_tray_icon, args=(port,), daemon=True)
    tray_thread.start()

    # Auto-open browser
    if settings.get('auto_open_browser', True):
        threading.Timer(1.5, webbrowser.open, args=["http://127.0.0.1:{}".format(port)]).start()

    print("{} v{} starting on http://127.0.0.1:{}".format(APP_NAME, VERSION, port))

    socketio.run(app, host='127.0.0.1', port=port, debug=False, allow_unsafe_werkzeug=True)
