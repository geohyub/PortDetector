"""History / Event Log panel."""

from __future__ import annotations

import csv

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QFileDialog,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor

from desktop.theme import Colors, Fonts
from backend.utils.monitoring_presenter import (
    build_ports_text,
    build_status_reason,
    derive_event_severity,
    importance_label,
    severity_label,
)


EVENT_FILTERS = [
    ("All events", None),
    ("Attention only", ["delayed", "disconnected"]),
    ("Disconnects", ["disconnected"]),
    ("High latency", ["delayed"]),
    ("Recoveries", ["connected"]),
]

EVENT_LABELS = {
    "connected": "Recovered",
    "delayed": "High latency",
    "disconnected": "Disconnected",
}

SEVERITY_COLORS = {
    "info": Colors.ACCENT,
    "advisory": Colors.WARNING,
    "warning": Colors.WARNING,
    "critical": Colors.DISCONNECTED,
    "emergency": Colors.DISCONNECTED,
}


class HistoryPanel(QWidget):
    def __init__(self, log_service, config_service, parent=None):
        super().__init__(parent)
        self._log_service = log_service
        self._config_service = config_service
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("Event History")
        title.setStyleSheet(
            f"font-size: {Fonts.SIZE_XL}px; font-weight: 700; color: {Colors.TEXT}; background: transparent;"
        )
        header.addWidget(title)
        header.addStretch()

        filter_label = QLabel("Device:")
        filter_label.setStyleSheet(
            f"font-size: {Fonts.SIZE_SM}px; color: {Colors.TEXT_DIM}; background: transparent;"
        )
        header.addWidget(filter_label)

        self._device_filter = QComboBox()
        self._device_filter.setFixedWidth(200)
        self._device_filter.addItem("All devices", "")
        self._device_filter.currentIndexChanged.connect(self._refresh)
        header.addWidget(self._device_filter)

        event_label = QLabel("Event:")
        event_label.setStyleSheet(
            f"font-size: {Fonts.SIZE_SM}px; color: {Colors.TEXT_DIM}; background: transparent;"
        )
        header.addWidget(event_label)

        self._event_filter = QComboBox()
        self._event_filter.setFixedWidth(170)
        for label, event_list in EVENT_FILTERS:
            self._event_filter.addItem(label, event_list)
        self._event_filter.currentIndexChanged.connect(self._refresh)
        header.addWidget(self._event_filter)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setFixedHeight(30)
        refresh_btn.clicked.connect(self._refresh)
        header.addWidget(refresh_btn)

        export_btn = QPushButton("Export CSV")
        export_btn.setFixedHeight(30)
        export_btn.clicked.connect(self._export_csv)
        header.addWidget(export_btn)

        layout.addLayout(header)

        self._summary = QLabel("")
        self._summary.setWordWrap(True)
        self._summary.setStyleSheet(
            f"""
            QLabel {{
                background-color: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
                padding: 10px 12px;
                color: {Colors.TEXT_DIM};
                font-size: {Fonts.SIZE_SM}px;
            }}
        """
        )
        layout.addWidget(self._summary)

        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels([
            "Timestamp", "Device", "Change", "Severity", "Why It Matters", "RTT (ms)",
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(0, 170)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(2, 120)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(3, 90)
        self._table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(5, 90)
        self._table.setShowGrid(False)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.verticalHeader().setVisible(False)
        self._table.setStyleSheet(f"QTableWidget {{ alternate-background-color: {Colors.BG_ALT}; }}")
        layout.addWidget(self._table, 1)

        page_row = QHBoxLayout()
        page_row.addStretch()
        self._page_label = QLabel("Page 1")
        self._page_label.setStyleSheet(
            f"font-size: {Fonts.SIZE_SM}px; color: {Colors.TEXT_DIM}; background: transparent;"
        )
        page_row.addWidget(self._page_label)

        self._prev_btn = QPushButton("Prev")
        self._prev_btn.setFixedWidth(60)
        self._prev_btn.setEnabled(False)
        self._prev_btn.clicked.connect(self._prev_page)
        page_row.addWidget(self._prev_btn)

        self._next_btn = QPushButton("Next")
        self._next_btn.setFixedWidth(60)
        self._next_btn.clicked.connect(self._next_page)
        page_row.addWidget(self._next_btn)

        layout.addLayout(page_row)

        self._page = 0
        self._page_size = 100

    def refresh_device_filter(self):
        current = self._device_filter.currentData()
        self._device_filter.blockSignals(True)
        self._device_filter.clear()
        self._device_filter.addItem("All devices", "")
        for dev in self._config_service.get_devices():
            label = f"{dev.name} ({dev.ip})"
            self._device_filter.addItem(label, dev.id)
        for i in range(self._device_filter.count()):
            if self._device_filter.itemData(i) == current:
                self._device_filter.setCurrentIndex(i)
                break
        self._device_filter.blockSignals(False)

    def _refresh(self):
        self._page = 0
        self._load_page()

    def _prev_page(self):
        if self._page > 0:
            self._page -= 1
            self._load_page()

    def _next_page(self):
        self._page += 1
        self._load_page()

    def _device_lookup(self):
        devices = {}
        for dev in self._config_service.get_devices():
            devices[dev.id] = {
                'name': dev.name,
                'ip': dev.ip,
                'importance': getattr(dev, 'importance', 'standard'),
                'category': dev.category,
                'ports': list(dev.ports),
            }
        return devices

    def _selected_filters(self):
        return (
            self._device_filter.currentData() or None,
            self._event_filter.currentData() or None,
        )

    def _build_entry_view(self, entry: dict, device_lookup: dict):
        device_info = device_lookup.get(entry.get('device_id', ''), {})
        event = entry.get('event', '')
        importance = entry.get('importance') or device_info.get('importance', 'standard')
        severity = derive_event_severity(event, importance)

        delay_threshold = self._config_service.get_settings().get('delay_threshold_ms', 200)
        old_status = entry.get('old_status')
        if event == 'connected' and old_status in EVENT_LABELS:
            reason = f"Recovered after {EVENT_LABELS[old_status].lower()}."
        else:
            reason = entry.get('reason') or build_status_reason(event, entry.get('rtt_ms'), delay_threshold)
        ports = entry.get('ports') or device_info.get('ports') or []
        if event in ('delayed', 'disconnected') and ports:
            reason = f"{reason} Reference ports: {build_ports_text(ports)}."

        device_name = entry.get('device_name') or device_info.get('name') or entry.get('device_id', '')
        ip = entry.get('ip') or device_info.get('ip', '')
        device_text = f"{device_name} ({ip})" if ip else device_name

        return {
            'timestamp': entry.get('timestamp', ''),
            'device': device_text,
            'change': EVENT_LABELS.get(event, event.title()),
            'severity': severity,
            'severity_label': severity_label(severity),
            'detail': f"{importance_label(importance)} device. {reason}",
            'rtt': entry.get('rtt_ms'),
        }

    def _update_summary(self, all_entries):
        counts = {
            'total': len(all_entries),
            'disconnected': 0,
            'delayed': 0,
            'connected': 0,
        }
        for entry in all_entries:
            event = entry.get('event')
            if event in counts:
                counts[event] += 1

        self._summary.setText(
            f"In current filter: {counts['total']:,} events | "
            f"{counts['disconnected']:,} disconnects | "
            f"{counts['delayed']:,} latency events | "
            f"{counts['connected']:,} recoveries"
        )

    def _load_page(self):
        device_id, event_filter = self._selected_filters()
        entries = self._log_service.get_history(
            limit=self._page_size,
            offset=self._page * self._page_size,
            device_id=device_id,
            events=event_filter,
        )
        summary_entries = self._log_service.get_all_entries(
            device_id=device_id,
            events=event_filter,
        )
        self._update_summary(summary_entries)

        device_lookup = self._device_lookup()
        mono = QFont(Fonts.MONO, Fonts.SIZE_SM)
        self._table.setRowCount(0)

        for entry in entries:
            view = self._build_entry_view(entry, device_lookup)
            severity = view['severity']
            color = QColor(SEVERITY_COLORS.get(severity, Colors.TEXT_DIM))

            row = self._table.rowCount()
            self._table.insertRow(row)

            ts_item = QTableWidgetItem(view['timestamp'])
            ts_item.setFont(mono)
            self._table.setItem(row, 0, ts_item)

            self._table.setItem(row, 1, QTableWidgetItem(view['device']))

            change_item = QTableWidgetItem(view['change'])
            change_item.setForeground(color)
            self._table.setItem(row, 2, change_item)

            severity_item = QTableWidgetItem(view['severity_label'])
            severity_item.setForeground(color)
            self._table.setItem(row, 3, severity_item)

            detail_item = QTableWidgetItem(view['detail'])
            self._table.setItem(row, 4, detail_item)

            rtt = view['rtt']
            rtt_item = QTableWidgetItem(f"{rtt:,}" if rtt is not None else "--")
            rtt_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            rtt_item.setFont(mono)
            self._table.setItem(row, 5, rtt_item)

        self._page_label.setText(f"Page {self._page + 1}")
        self._prev_btn.setEnabled(self._page > 0)
        self._next_btn.setEnabled(len(entries) == self._page_size)

    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export History",
            "history_filtered.csv",
            "CSV Files (*.csv)",
        )
        if not path:
            return

        device_id, event_filter = self._selected_filters()
        entries = self._log_service.get_all_entries(
            device_id=device_id,
            events=event_filter,
        )
        device_lookup = self._device_lookup()

        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Device", "Change", "Severity", "Why It Matters", "RTT (ms)"])
            for entry in entries:
                view = self._build_entry_view(entry, device_lookup)
                writer.writerow([
                    view['timestamp'],
                    view['device'],
                    view['change'],
                    view['severity_label'],
                    view['detail'],
                    "" if view['rtt'] is None else view['rtt'],
                ])
