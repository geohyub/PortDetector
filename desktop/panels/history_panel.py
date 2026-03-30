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
from desktop.i18n import t
from backend.utils.monitoring_presenter import (
    build_ports_text,
    build_status_reason,
    derive_event_severity,
    importance_label,
    severity_label,
)


EVENT_FILTERS = [
    ("all_events", None),
    ("attention_only", ["delayed", "disconnected"]),
    ("disconnects", ["disconnected"]),
    ("high_latency", ["delayed"]),
    ("recoveries", ["connected"]),
]

EVENT_LABELS = {
    "connected": "event_connected",
    "delayed": "event_delayed",
    "disconnected": "event_disconnected",
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
        self._title_label = QLabel(t("history.title"))
        self._title_label.setStyleSheet(
            f"font-size: {Fonts.SIZE_XL}px; font-weight: 700; color: {Colors.TEXT}; background: transparent;"
        )
        header.addWidget(self._title_label)
        header.addStretch()

        self._filter_label = QLabel(t("history.device"))
        self._filter_label.setStyleSheet(
            f"font-size: {Fonts.SIZE_SM}px; color: {Colors.TEXT_DIM}; background: transparent;"
        )
        header.addWidget(self._filter_label)

        self._device_filter = QComboBox()
        self._device_filter.setFixedWidth(200)
        self._device_filter.addItem(t("history.all_devices"), "")
        self._device_filter.currentIndexChanged.connect(self._refresh)
        header.addWidget(self._device_filter)

        self._event_label = QLabel(t("history.event"))
        self._event_label.setStyleSheet(
            f"font-size: {Fonts.SIZE_SM}px; color: {Colors.TEXT_DIM}; background: transparent;"
        )
        header.addWidget(self._event_label)

        self._event_filter = QComboBox()
        self._event_filter.setFixedWidth(170)
        for key, event_list in EVENT_FILTERS:
            self._event_filter.addItem(t(f"history.{key}"), event_list)
        self._event_filter.currentIndexChanged.connect(self._refresh)
        header.addWidget(self._event_filter)

        self._refresh_btn = QPushButton(t("history.refresh"))
        self._refresh_btn.setFixedHeight(30)
        self._refresh_btn.clicked.connect(self._refresh)
        header.addWidget(self._refresh_btn)

        self._export_btn = QPushButton(t("history.export_csv"))
        self._export_btn.setFixedHeight(30)
        self._export_btn.clicked.connect(self._export_csv)
        header.addWidget(self._export_btn)

        layout.addLayout(header)

        self._guide_label = QLabel(t("guide.history"))
        self._guide_label.setWordWrap(True)
        self._guide_label.setStyleSheet(
            f"font-size: {Fonts.SIZE_XS}px; color: {Colors.TEXT_MUTED}; background: transparent; padding-bottom: 4px;"
        )
        layout.addWidget(self._guide_label)

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
            t("history.col_timestamp"), t("history.col_device"), t("history.col_change"),
            t("history.col_severity"), t("history.col_detail"), t("history.col_rtt"),
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
        self._page_label = QLabel(t("history.page", n=1))
        self._page_label.setStyleSheet(
            f"font-size: {Fonts.SIZE_SM}px; color: {Colors.TEXT_DIM}; background: transparent;"
        )
        page_row.addWidget(self._page_label)

        self._prev_btn = QPushButton(t("history.prev"))
        self._prev_btn.setFixedWidth(60)
        self._prev_btn.setEnabled(False)
        self._prev_btn.clicked.connect(self._prev_page)
        page_row.addWidget(self._prev_btn)

        self._next_btn = QPushButton(t("history.next"))
        self._next_btn.setFixedWidth(60)
        self._next_btn.clicked.connect(self._next_page)
        page_row.addWidget(self._next_btn)

        layout.addLayout(page_row)

        self._page = 0
        self._page_size = 100

    def retranslate(self):
        """Update all translatable strings to the current language."""
        self._title_label.setText(t("history.title"))
        self._guide_label.setText(t("guide.history"))
        self._filter_label.setText(t("history.device"))
        self._event_label.setText(t("history.event"))
        self._refresh_btn.setText(t("history.refresh"))
        self._export_btn.setText(t("history.export_csv"))
        self._prev_btn.setText(t("history.prev"))
        self._next_btn.setText(t("history.next"))
        self._page_label.setText(t("history.page", n=self._page + 1))

        # Re-populate event filter combo with translated labels
        current_event_idx = self._event_filter.currentIndex()
        self._event_filter.blockSignals(True)
        self._event_filter.clear()
        for key, event_list in EVENT_FILTERS:
            self._event_filter.addItem(t(f"history.{key}"), event_list)
        self._event_filter.setCurrentIndex(current_event_idx)
        self._event_filter.blockSignals(False)

        # Re-populate device filter (keep "All devices" translated)
        self.refresh_device_filter()

        # Update table headers
        self._table.setHorizontalHeaderLabels([
            t("history.col_timestamp"), t("history.col_device"), t("history.col_change"),
            t("history.col_severity"), t("history.col_detail"), t("history.col_rtt"),
        ])

    def refresh_device_filter(self):
        current = self._device_filter.currentData()
        self._device_filter.blockSignals(True)
        self._device_filter.clear()
        self._device_filter.addItem(t("history.all_devices"), "")
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
            reason = build_status_reason(event, entry.get('rtt_ms'), delay_threshold)
        else:
            reason = entry.get('reason') or build_status_reason(event, entry.get('rtt_ms'), delay_threshold)

        device_name = entry.get('device_name') or device_info.get('name') or entry.get('device_id', '')
        ip = entry.get('ip') or device_info.get('ip', '')
        device_text = f"{device_name} ({ip})" if ip else device_name

        event_label_key = EVENT_LABELS.get(event)
        change_text = t(f"history.{event_label_key}") if event_label_key else event.title()

        return {
            'timestamp': entry.get('timestamp', ''),
            'device': device_text,
            'change': change_text,
            'severity': severity,
            'severity_label': severity_label(severity),
            'detail': f"{importance_label(importance)}. {reason}",
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
            t("history.summary",
              total=counts['total'],
              disc=counts['disconnected'],
              delayed=counts['delayed'],
              conn=counts['connected'])
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
        self._table.setRowCount(0)

        for entry in entries:
            view = self._build_entry_view(entry, device_lookup)
            severity = view['severity']
            color = QColor(SEVERITY_COLORS.get(severity, Colors.TEXT_DIM))

            row = self._table.rowCount()
            self._table.insertRow(row)

            ts_item = QTableWidgetItem(view['timestamp'])
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
            self._table.setItem(row, 5, rtt_item)

        self._page_label.setText(t("history.page", n=self._page + 1))
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
            writer.writerow([
                t("history.col_timestamp"), t("history.col_device"), t("history.col_change"),
                t("history.col_severity"), t("history.col_detail"), t("history.col_rtt"),
            ])
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
