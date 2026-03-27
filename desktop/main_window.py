"""PortDetector MainWindow — sidebar navigation + stacked panels."""

import os
import sys

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget, QFrame, QMessageBox,
    QSystemTrayIcon, QMenu,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QPixmap, QImage, QAction

from config import APP_NAME, VERSION
from desktop.theme import Colors, Fonts, STYLESHEET
from desktop.panels.dashboard_panel import DashboardPanel
from desktop.panels.scanner_panel import ScannerPanel
from desktop.panels.discovery_panel import DiscoveryPanel
from desktop.panels.traceroute_panel import TraceroutePanel
from desktop.panels.interfaces_panel import InterfacesPanel
from desktop.panels.serial_panel import SerialPanel
from desktop.panels.history_panel import HistoryPanel
from desktop.panels.report_panel import ReportPanel
from desktop.panels.settings_panel import SettingsPanel
from desktop.dialogs.device_dialog import DeviceDialog
from desktop.workers.ping_worker import PingWorkerThread
from desktop.workers.interface_worker import InterfaceWorkerThread
from desktop.workers.serial_worker import SerialWorkerThread


NAV_ITEMS = [
    ("Dashboard", 0),
    ("Scanner", 1),
    ("Discovery", 2),
    ("Traceroute", 3),
    ("Interfaces", 4),
    ("Serial/NMEA", 5),
    ("History", 6),
    ("Report", 7),
    ("Settings", 8),
]


class MainWindow(QMainWindow):
    def __init__(self, config_service, log_service, traffic_service,
                 profile_service, alert_service, uptime_service):
        super().__init__()
        self._config_service = config_service
        self._log_service = log_service
        self._traffic_service = traffic_service
        self._profile_service = profile_service
        self._alert_service = alert_service
        self._uptime_service = uptime_service

        self._ping_worker = None
        self._interface_worker = None
        self._serial_worker = None

        self.setWindowTitle(f"{APP_NAME} v{VERSION}")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)
        self.setStyleSheet(STYLESHEET)

        self._build_ui()
        self._setup_workers()
        self._setup_tray()

        # Initial data load
        self._refresh_devices()
        self._history_panel.refresh_device_filter()
        self._history_panel._refresh()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # Logo area
        logo_widget = QWidget()
        logo_widget.setStyleSheet("background: transparent;")
        logo_layout = QVBoxLayout(logo_widget)
        logo_layout.setContentsMargins(16, 16, 16, 12)
        logo_layout.setSpacing(2)

        app_name = QLabel(APP_NAME)
        app_name.setStyleSheet(f"font-size: {Fonts.SIZE_LG}px; font-weight: 700; color: {Colors.ACCENT}; background: transparent;")
        logo_layout.addWidget(app_name)

        ver_label = QLabel(f"v{VERSION}")
        ver_label.setStyleSheet(f"font-size: {Fonts.SIZE_XS}px; color: {Colors.TEXT_MUTED}; background: transparent;")
        logo_layout.addWidget(ver_label)

        sidebar_layout.addWidget(logo_widget)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {Colors.BORDER};")
        sidebar_layout.addWidget(sep)

        # Nav buttons
        self._nav_buttons = []
        for label, idx in NAV_ITEMS:
            btn = QPushButton(label)
            btn.setProperty("active", idx == 0)
            btn.clicked.connect(lambda checked, i=idx: self._switch_page(i))
            sidebar_layout.addWidget(btn)
            self._nav_buttons.append(btn)

        sidebar_layout.addStretch()

        # Traffic status
        self._traffic_label = QLabel()
        self._traffic_label.setStyleSheet(f"font-size: {Fonts.SIZE_XS}px; color: {Colors.TEXT_MUTED}; padding: 8px 16px; background: transparent;")
        if self._traffic_service and self._traffic_service.is_available():
            self._traffic_label.setText("Traffic: Active")
        else:
            self._traffic_label.setText("Traffic: Disabled")
        sidebar_layout.addWidget(self._traffic_label)

        root.addWidget(sidebar)

        # Main content
        content_area = QVBoxLayout()
        content_area.setContentsMargins(0, 0, 0, 0)
        content_area.setSpacing(0)

        self._stack = QStackedWidget()

        # 0: Dashboard
        self._dashboard = DashboardPanel()
        self._dashboard.add_device_requested.connect(self._add_device)
        self._dashboard.device_selected.connect(self._on_device_selected)
        self._stack.addWidget(self._dashboard)

        # 1: Scanner
        self._scanner = ScannerPanel()
        self._stack.addWidget(self._scanner)

        # 2: Discovery
        self._discovery = DiscoveryPanel()
        self._stack.addWidget(self._discovery)

        # 3: Traceroute
        self._traceroute = TraceroutePanel()
        self._stack.addWidget(self._traceroute)

        # 4: Interfaces
        self._interfaces = InterfacesPanel()
        self._stack.addWidget(self._interfaces)

        # 5: Serial/NMEA
        self._serial = SerialPanel()
        self._stack.addWidget(self._serial)

        # 6: History
        self._history_panel = HistoryPanel(self._log_service, self._config_service)
        self._stack.addWidget(self._history_panel)

        # 7: Report
        self._report = ReportPanel(self._uptime_service, self._config_service)
        self._stack.addWidget(self._report)

        # 8: Settings
        self._settings = SettingsPanel(self._config_service, self._profile_service)
        self._settings.settings_changed.connect(self._on_settings_changed)
        self._settings.profile_loaded.connect(self._on_profile_loaded)
        self._settings.preset_loaded.connect(self._on_profile_loaded)
        self._stack.addWidget(self._settings)

        content_area.addWidget(self._stack, 1)
        root.addLayout(content_area, 1)

    def _switch_page(self, idx):
        self._stack.setCurrentIndex(idx)
        for i, btn in enumerate(self._nav_buttons):
            btn.setProperty("active", i == idx)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        if idx == 6:  # History
            self._history_panel.refresh_device_filter()
            self._history_panel._refresh()

    def _setup_workers(self):
        settings = self._config_service.get_settings()

        # Ping worker
        self._ping_worker = PingWorkerThread(
            self._config_service,
            self._log_service,
            delay_threshold_ms=settings.get('delay_threshold_ms', 200),
        )
        self._ping_worker.signals.batch_update.connect(self._on_ping_update)
        self._ping_worker.signals.status_change.connect(self._on_status_change)
        self._ping_worker.set_interval(settings.get('ping_interval_seconds', 5))
        self._ping_worker.start()

        # Interface worker
        self._interface_worker = InterfaceWorkerThread(
            interval=settings.get('interface_poll_seconds', 3)
        )
        self._interface_worker.update.connect(self._on_interface_update)
        self._interface_worker.start()

        # Serial worker
        self._serial_worker = SerialWorkerThread(interval=5)
        self._serial_worker.update.connect(self._on_serial_update)
        self._serial_worker.start()

        # RTT graph refresh timer
        self._graph_timer = QTimer(self)
        self._graph_timer.timeout.connect(self._refresh_rtt_graph)
        self._graph_timer.start(5000)

        # Apply alert settings
        self._sync_alert_settings(settings)

    def _setup_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        self._tray = QSystemTrayIcon(self)
        img = QImage(64, 64, QImage.Format.Format_ARGB32)
        img.fill(Qt.GlobalColor.transparent)
        from PySide6.QtGui import QPainter, QBrush
        painter = QPainter(img)
        painter.setBrush(QBrush(Qt.GlobalColor.cyan))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(4, 4, 56, 56)
        painter.end()
        self._tray.setIcon(QIcon(QPixmap.fromImage(img)))
        self._tray.setToolTip(f"{APP_NAME} v{VERSION}")

        menu = QMenu()
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.showNormal)
        menu.addAction(show_action)
        quit_action = QAction("Exit", self)
        quit_action.triggered.connect(self._quit)
        menu.addAction(quit_action)
        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()

    # ── Event handlers ──

    def _on_ping_update(self, results):
        self._dashboard.update_ping_data(results)

        # Feed alert service
        for r in results:
            dev_id = r.get('device_id', '')
            status = r.get('status', '')
            alert_info = self._alert_service.on_status_update(dev_id, status)
            if alert_info.get('escalated'):
                self._handle_alert_escalation(dev_id, alert_info)

    def _handle_alert_escalation(self, device_id, alert_info):
        """Handle escalated alert — sound + tray notification."""
        level = alert_info.get('level', 'warning')
        count = alert_info.get('count', 0)

        device = self._config_service.get_device(device_id)
        name = device.name if device else device_id

        # Sound
        self._alert_service.play_alert_sound_async(level)

        # Tray notification
        if hasattr(self, '_tray'):
            if level == 'recovered':
                msg = f"{name}: Recovered (back online)"
                icon = QSystemTrayIcon.MessageIcon.Information
            elif level == 'emergency':
                msg = f"{name}: EMERGENCY ({count} consecutive failures)"
                icon = QSystemTrayIcon.MessageIcon.Critical
            elif level == 'critical':
                msg = f"{name}: CRITICAL ({count} consecutive failures)"
                icon = QSystemTrayIcon.MessageIcon.Critical
            else:
                msg = f"{name}: Disconnected"
                icon = QSystemTrayIcon.MessageIcon.Warning

            self._tray.showMessage(f"{APP_NAME} Alert", msg, icon, 5000)

    def _on_status_change(self, data):
        # Basic tray notification (non-escalation path)
        settings = self._config_service.get_settings()
        if not settings.get('alert_enabled', True):
            return
        # Escalated alerts handled in _on_ping_update, this is for non-escalated
        pass

    def _on_interface_update(self, interfaces):
        self._interfaces.update_interfaces(interfaces)

    def _on_serial_update(self, results):
        self._serial.update_serial_data(results)

    def _refresh_rtt_graph(self):
        if self._ping_worker:
            history = self._ping_worker.get_rtt_history()
            self._dashboard.update_rtt_graph(history)

    def _on_settings_changed(self, data):
        if self._ping_worker:
            self._ping_worker.set_interval(data.get('ping_interval_seconds', 5))
            self._ping_worker.set_threshold(data.get('delay_threshold_ms', 200))
        if self._interface_worker:
            self._interface_worker.set_interval(data.get('interface_poll_seconds', 3))
        self._sync_alert_settings(data)

    def _sync_alert_settings(self, settings):
        self._alert_service.set_sound_enabled(settings.get('sound_enabled', True))
        self._alert_service.set_escalation_enabled(settings.get('escalation_enabled', True))

    def _on_profile_loaded(self):
        """Reload devices after profile/preset change."""
        self._refresh_devices()
        self._history_panel.refresh_device_filter()

    def _refresh_devices(self):
        devices = self._config_service.get_devices()
        self._dashboard.set_devices(devices)

    def _add_device(self):
        dialog = DeviceDialog(self)
        if dialog.exec() == DeviceDialog.DialogCode.Accepted:
            data = dialog.get_result()
            if data:
                from backend.models.device import Device
                device = Device.from_dict(data)
                try:
                    self._config_service.add_device(device)
                    self._refresh_devices()
                except ValueError as e:
                    QMessageBox.warning(self, "Validation Error", str(e))

    def _on_device_selected(self, device_id):
        device = self._config_service.get_device(device_id)
        if device:
            self._scanner.set_target_ip(device.ip)

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.showNormal()
            self.activateWindow()

    def _quit(self):
        self._stop_workers()
        from PySide6.QtWidgets import QApplication
        QApplication.quit()

    def _stop_workers(self):
        if self._ping_worker:
            self._ping_worker.stop()
            self._ping_worker.wait(3000)
        if self._interface_worker:
            self._interface_worker.stop()
            self._interface_worker.wait(3000)
        if self._serial_worker:
            self._serial_worker.stop()
            self._serial_worker.wait(3000)
        if self._traffic_service:
            self._traffic_service.stop()

    def closeEvent(self, event):
        if hasattr(self, '_tray') and self._tray.isVisible():
            self.hide()
            event.ignore()
        else:
            self._stop_workers()
            event.accept()
