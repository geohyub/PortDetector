"""PortDetector MainWindow — sidebar navigation + stacked panels."""

import os
from datetime import datetime

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget, QFrame,
    QSystemTrayIcon, QMenu,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QPixmap, QImage, QAction

from config import APP_NAME, VERSION
from desktop.theme import Colors, Fonts, STYLESHEET
from desktop.i18n import t, set_language, get_language
from desktop.panels.dashboard_panel import DashboardPanel
from desktop.panels.scanner_panel import ScannerPanel
from desktop.panels.discovery_panel import DiscoveryPanel
from desktop.panels.traceroute_panel import TraceroutePanel
from desktop.panels.interfaces_panel import InterfacesPanel
from desktop.panels.serial_panel import SerialPanel
from desktop.panels.history_panel import HistoryPanel
from desktop.panels.report_panel import ReportPanel
from desktop.panels.settings_panel import SettingsPanel
from desktop.panels.network_map_panel import NetworkMapPanel
from desktop.dialogs.device_dialog import DeviceDialog
from desktop.workers.ping_worker import PingWorkerThread
from desktop.workers.interface_worker import InterfaceWorkerThread
from desktop.workers.serial_worker import SerialWorkerThread
from backend.utils.monitoring_presenter import (
    build_action_text,
    build_ports_text,
    build_status_label,
    build_status_reason,
    derive_runtime_severity,
    format_relative_time,
    importance_label,
    importance_weight,
    severity_label,
    severity_rank,
)


NAV_KEYS = [
    "nav.dashboard", "nav.scanner", "nav.discovery", "nav.traceroute",
    "nav.interfaces", "nav.serial", "nav.networkmap",
    "nav.history", "nav.report", "nav.settings",
]


class MainWindow(QMainWindow):
    def __init__(self, config_service, log_service, traffic_service,
                 profile_service, alert_service, backup_service, uptime_service):
        super().__init__()
        self._config_service = config_service
        self._log_service = log_service
        self._traffic_service = traffic_service
        self._profile_service = profile_service
        self._alert_service = alert_service
        self._backup_service = backup_service
        self._uptime_service = uptime_service

        self._ping_worker = None
        self._interface_worker = None
        self._serial_worker = None
        self._alerts_enabled = True
        self._delay_threshold_ms = 200
        self._device_states = {}
        self._last_status_changes = {}
        self._selected_device_id = None

        self.setWindowTitle(f"{APP_NAME} v{VERSION}")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)
        self.setStyleSheet(STYLESHEET)

        self._build_ui()
        self._setup_workers()
        self._setup_tray()

        # Initial data load
        self._refresh_devices()
        self._update_dashboard_context()
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
        for idx, key in enumerate(NAV_KEYS):
            btn = QPushButton(t(key))
            btn.setProperty("active", idx == 0)
            btn.setProperty("nav_key", key)
            btn.clicked.connect(lambda checked, i=idx: self._switch_page(i))
            sidebar_layout.addWidget(btn)
            self._nav_buttons.append(btn)

        sidebar_layout.addStretch()

        # Traffic status
        self._traffic_label = QLabel()
        self._traffic_label.setStyleSheet(f"font-size: {Fonts.SIZE_XS}px; color: {Colors.TEXT_MUTED}; padding: 8px 16px; background: transparent;")
        if self._traffic_service and self._traffic_service.is_available():
            self._traffic_label.setText(t("common.traffic_active"))
        else:
            self._traffic_label.setText(t("common.traffic_disabled"))
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
        self._dashboard.scan_device_requested.connect(self._open_device_in_scanner)
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
        self._serial.monitored_ports_changed.connect(self._on_serial_ports_changed)
        self._stack.addWidget(self._serial)

        # 6: Network Map
        from backend.services.network_map_service import NetworkMapService
        self._map_service = NetworkMapService(
            os.path.join(self._config_service._data_dir)
        )
        self._network_map = NetworkMapPanel(self._config_service, self._map_service)
        self._stack.addWidget(self._network_map)

        # 7: History
        self._history_panel = HistoryPanel(self._log_service, self._config_service)
        self._stack.addWidget(self._history_panel)

        # 8: Report
        self._report = ReportPanel(self._uptime_service, self._config_service)
        self._stack.addWidget(self._report)

        # 9: Settings
        self._settings = SettingsPanel(
            self._config_service,
            self._profile_service,
            self._backup_service,
        )
        self._settings.settings_changed.connect(self._on_settings_changed)
        self._settings.profile_loaded.connect(self._on_profile_loaded)
        self._settings.preset_loaded.connect(self._on_profile_loaded)
        self._settings.language_changed.connect(self._on_language_changed)
        self._stack.addWidget(self._settings)

        content_area.addWidget(self._stack, 1)
        root.addLayout(content_area, 1)

    def _switch_page(self, idx):
        self._stack.setCurrentIndex(idx)
        for i, btn in enumerate(self._nav_buttons):
            btn.setProperty("active", i == idx)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        if idx == 7:  # History
            self._history_panel.refresh_device_filter()
            self._history_panel._refresh()

    def _on_language_changed(self, lang: str):
        """Re-translate all UI text when language changes."""
        set_language(lang)
        # Save to settings
        self._config_service.update_settings({'language': lang})

        # Sidebar nav buttons
        for btn in self._nav_buttons:
            key = btn.property("nav_key")
            if key:
                btn.setText(t(key))

        # Traffic label
        if self._traffic_service and self._traffic_service.is_available():
            self._traffic_label.setText(t("common.traffic_active"))
        else:
            self._traffic_label.setText(t("common.traffic_disabled"))

        # Retranslate all panels
        self._dashboard.retranslate()
        self._scanner.retranslate()
        self._discovery.retranslate()
        self._traceroute.retranslate()
        self._interfaces.retranslate()
        self._serial.retranslate()
        self._network_map.retranslate()
        self._history_panel.retranslate()
        self._report.retranslate()
        self._settings.retranslate()

        # Refresh dynamic content
        self._update_dashboard_context()

        # Tray menu
        if hasattr(self, '_tray'):
            self._setup_tray()

    def _setup_workers(self):
        settings = self._config_service.get_settings()
        self._delay_threshold_ms = settings.get('delay_threshold_ms', 200)

        # Ping worker
        self._ping_worker = PingWorkerThread(
            self._config_service,
            self._log_service,
            delay_threshold_ms=self._delay_threshold_ms,
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
        self._serial_worker.set_ports(self._serial.get_monitored_ports())
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

        if not hasattr(self, '_tray'):
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
            self._tray.activated.connect(self._on_tray_activated)

        self._tray.setToolTip(f"{APP_NAME} v{VERSION}")

        menu = QMenu()
        show_action = QAction(t("tray.show"), self)
        show_action.triggered.connect(self.showNormal)
        menu.addAction(show_action)
        quit_action = QAction(t("tray.exit"), self)
        quit_action.triggered.connect(self._quit)
        menu.addAction(quit_action)
        self._tray.setContextMenu(menu)
        self._tray.show()

    # ── Event handlers ──

    def _on_ping_update(self, results):
        devices_by_id = {device.id: device for device in self._config_service.get_devices()}
        for result in results:
            dev_id = result.get('device_id', '')
            status = result.get('status', 'unknown')
            rtt_ms = result.get('rtt_ms')
            device = devices_by_id.get(dev_id)

            alert_info = self._alert_service.on_status_update(dev_id, status)
            issue_state = self._alert_service.get_issue_state(dev_id)

            self._device_states[dev_id] = {
                'status': status,
                'rtt_ms': rtt_ms,
                'timestamp': result.get('timestamp'),
                'fail_count': issue_state.get('count', 0),
                'issue_status': issue_state.get('issue_status'),
                'severity': derive_runtime_severity(
                    status,
                    getattr(device, 'importance', 'standard') if device else 'standard',
                    issue_state.get('count', 0),
                ),
                'reason': build_status_reason(status, rtt_ms, self._delay_threshold_ms),
            }

            if alert_info.get('escalated') and self._alerts_enabled:
                self._handle_alert_escalation(dev_id, alert_info)

        self._update_dashboard_context()

    def _handle_alert_escalation(self, device_id, alert_info):
        """Handle escalated alert — sound + tray notification."""
        level = alert_info.get('level', 'warning')
        count = alert_info.get('count', 0)
        issue_status = alert_info.get('issue_status')

        device = self._config_service.get_device(device_id)
        name = device.name if device else device_id

        # Sound
        self._alert_service.play_alert_sound_async(level)

        # Tray notification
        if hasattr(self, '_tray'):
            if level == 'recovered':
                if issue_status == 'delayed':
                    msg = t("alert.recovered_latency", name=name)
                else:
                    msg = t("alert.recovered", name=name)
                icon = QSystemTrayIcon.MessageIcon.Information
            elif issue_status == 'delayed':
                if level == 'critical':
                    msg = t("alert.critical_latency", name=name, count=count)
                    icon = QSystemTrayIcon.MessageIcon.Critical
                else:
                    msg = t("alert.warning_latency", name=name, count=count)
                    icon = QSystemTrayIcon.MessageIcon.Warning
            elif level == 'emergency':
                msg = t("alert.emergency", name=name, count=count)
                icon = QSystemTrayIcon.MessageIcon.Critical
            elif level == 'critical':
                msg = t("alert.critical", name=name, count=count)
                icon = QSystemTrayIcon.MessageIcon.Critical
            else:
                msg = t("alert.disconnected", name=name)
                icon = QSystemTrayIcon.MessageIcon.Warning

            self._tray.showMessage(f"{APP_NAME}", msg, icon, 5000)

    def _on_status_change(self, data):
        device_id = data.get('device_id', '')
        timestamp = data.get('timestamp')
        if device_id:
            self._last_status_changes[device_id] = timestamp
        if self._stack.currentIndex() == 7:
            self._history_panel._refresh()
        self._update_dashboard_context()

    def _on_interface_update(self, interfaces):
        self._interfaces.update_interfaces(interfaces)

    def _on_serial_update(self, results):
        self._serial.update_serial_data(results)

    def _refresh_rtt_graph(self):
        if self._ping_worker:
            history = self._ping_worker.get_rtt_history()
            selected = self._config_service.get_device(self._selected_device_id) if self._selected_device_id else None
            self._dashboard.update_rtt_graph(
                history,
                selected_device_id=self._selected_device_id,
                selected_device_name=selected.name if selected else None,
                delay_threshold_ms=self._delay_threshold_ms,
            )

    def _on_settings_changed(self, data):
        self._delay_threshold_ms = data.get('delay_threshold_ms', self._delay_threshold_ms)
        if self._ping_worker:
            self._ping_worker.set_interval(data.get('ping_interval_seconds', 5))
            self._ping_worker.set_threshold(data.get('delay_threshold_ms', 200))
        if self._interface_worker:
            self._interface_worker.set_interval(data.get('interface_poll_seconds', 3))
        self._sync_alert_settings(data)
        self._update_dashboard_context()
        self._refresh_rtt_graph()

    def _sync_alert_settings(self, settings):
        self._alerts_enabled = settings.get('alert_enabled', True)
        self._alert_service.set_sound_enabled(settings.get('sound_enabled', True))
        self._alert_service.set_escalation_enabled(settings.get('escalation_enabled', True))

    def _on_profile_loaded(self):
        """Reload devices after profile/preset change."""
        self._refresh_devices()
        self._history_panel.refresh_device_filter()
        self._update_dashboard_context()

    def _refresh_devices(self):
        devices = self._config_service.get_devices()
        self._dashboard.set_devices(devices)
        if devices:
            existing = {device.id for device in devices}
            if self._selected_device_id not in existing:
                self._selected_device_id = devices[0].id
        else:
            self._selected_device_id = None
        self._dashboard.set_selected_device(self._selected_device_id)
        self._update_dashboard_context()

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
                    from geoview_pyside6.widgets.confirm_dialog import ConfirmDialog

                    ConfirmDialog(t("common.validation_error"), str(e), confirm_text="OK", cancel_text="", dialog_type="warning", parent=self).exec()
    def _on_device_selected(self, device_id):
        self._selected_device_id = device_id
        self._dashboard.set_selected_device(device_id)
        device = self._config_service.get_device(device_id)
        if device:
            self._scanner.set_target(device.ip, device.ports)
        self._update_dashboard_context()
        self._refresh_rtt_graph()

    def _open_device_in_scanner(self, device_id):
        device = self._config_service.get_device(device_id)
        if not device:
            return
        self._scanner.set_target(device.ip, device.ports)
        self._switch_page(1)

    def _on_serial_ports_changed(self, ports):
        if self._serial_worker:
            self._serial_worker.set_ports(ports)

    def _build_device_snapshots(self):
        snapshots = []
        now = datetime.now()

        for device in self._config_service.get_devices():
            runtime = self._device_states.get(device.id, {})
            status = runtime.get('status', 'unknown')
            fail_count = runtime.get('fail_count', 0)
            severity = runtime.get('severity') or derive_runtime_severity(status, device.importance, fail_count)
            last_change = self._last_status_changes.get(device.id) or runtime.get('timestamp')

            if not device.enabled:
                status_label_text = t("status.disabled")
                reason = t("status.disabled_reason")
                severity = "info"
                last_change_text = t("status.disabled")
            else:
                status_label_text = build_status_label(status)
                reason = runtime.get('reason') or build_status_reason(
                    status,
                    runtime.get('rtt_ms'),
                    self._delay_threshold_ms,
                )
                last_change_text = (
                    format_relative_time(last_change, now)
                    if last_change else
                    t("status.waiting_first")
                )

            snapshots.append({
                'device_id': device.id,
                'id': device.id,
                'name': device.name,
                'ip': device.ip,
                'category': device.category or "Uncategorized",
                'importance': device.importance,
                'importance_label': importance_label(device.importance),
                'status': status,
                'status_label': status_label_text,
                'severity': severity,
                'reason': reason,
                'rtt_ms': runtime.get('rtt_ms'),
                'fail_count': fail_count,
                'last_change_text': last_change_text,
                'last_change_at': last_change,
                'ports': list(device.ports),
                'description': device.description,
                'action_text': build_action_text(status, device.ports, fail_count),
            })

        snapshots.sort(
            key=lambda snap: (
                -severity_rank(snap.get('severity')),
                -importance_weight(snap.get('importance')),
                snap.get('name', '').lower(),
            )
        )
        return snapshots

    def _build_overview(self, snapshots):
        if not snapshots:
            return {
                'severity': 'info',
                'headline': t("dash.no_devices_headline"),
                'detail': t("dash.no_devices_detail"),
                'context': t("dash.no_devices_context"),
            }

        critical_count = sum(
            1 for snap in snapshots
            if severity_rank(snap.get('severity')) >= severity_rank('critical')
        )
        attention_count = sum(1 for snap in snapshots if snap.get('status') in ('delayed', 'disconnected'))
        offline_count = sum(1 for snap in snapshots if snap.get('status') == 'disconnected')
        stable_count = sum(1 for snap in snapshots if snap.get('status') == 'connected')
        top_issue = next((snap for snap in snapshots if snap.get('status') in ('delayed', 'disconnected')), None)

        if critical_count > 0 and top_issue:
            headline = t("dash.immediate_attention", count=critical_count)
            detail = (
                f"{top_issue['name']}: {top_issue['status_label'].lower()}. "
                f"{top_issue['action_text']}"
            )
            severity = top_issue.get('severity', 'critical')
        elif attention_count > 0 and top_issue:
            headline = t("dash.needs_review", count=attention_count)
            detail = t("dash.review_detail",
                stable=stable_count, offline=offline_count,
                delayed=attention_count - offline_count, name=top_issue['name'])
            severity = top_issue.get('severity', 'warning')
        else:
            headline = t("dash.all_stable")
            detail = t("dash.all_stable_detail", count=stable_count)
            severity = "stable"

        settings = self._config_service.get_settings()
        context = t("dash.overview_context",
            interval=settings.get('ping_interval_seconds', 5),
            threshold=f"{self._delay_threshold_ms:,}")
        return {
            'severity': severity,
            'headline': headline,
            'detail': detail,
            'context': context,
        }

    def _build_device_detail(self, snapshots):
        if not snapshots:
            return {}

        selected_id = self._selected_device_id
        snapshot = next((snap for snap in snapshots if snap.get('device_id') == selected_id), None)
        if snapshot is None:
            snapshot = snapshots[0]
            self._selected_device_id = snapshot.get('device_id')
            self._dashboard.set_selected_device(self._selected_device_id)

        meta_parts = [
            snapshot.get('ip'),
            snapshot.get('category'),
            importance_label(snapshot.get('importance')),
        ]
        if snapshot.get('last_change_text'):
            meta_parts.append(snapshot['last_change_text'])

        description = snapshot.get('description') or ""
        ports_text = (
            f"Reference ports: {build_ports_text(snapshot.get('ports'))}. "
            f"Role: {description}" if description else
            f"Reference ports: {build_ports_text(snapshot.get('ports'))}"
        )

        return {
            'device_id': snapshot.get('device_id'),
            'name': snapshot.get('name'),
            'severity': snapshot.get('severity'),
            'status_label': snapshot.get('status_label'),
            'reason': snapshot.get('reason'),
            'meta_text': " | ".join(part for part in meta_parts if part),
            'ports_text': ports_text,
            'action_text': snapshot.get('action_text'),
            'has_ports': bool(snapshot.get('ports')),
        }

    def _update_dashboard_context(self):
        snapshots = self._build_device_snapshots()
        self._dashboard.update_device_snapshots(snapshots)
        self._dashboard.update_overview(self._build_overview(snapshots))
        self._dashboard.update_device_detail(self._build_device_detail(snapshots))
        self._refresh_rtt_graph()

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
        if hasattr(self, '_network_map'):
            self._network_map.stop_workers()
        if self._traffic_service:
            self._traffic_service.stop()

    def closeEvent(self, event):
        if hasattr(self, '_tray') and self._tray.isVisible():
            self.hide()
            event.ignore()
        else:
            self._stop_workers()
            event.accept()
