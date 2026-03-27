"""History / Event Log panel."""

import csv
import io

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QFileDialog,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor

from desktop.theme import Colors, Fonts


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

        # Header
        header = QHBoxLayout()
        title = QLabel("Event History")
        title.setStyleSheet(f"font-size: {Fonts.SIZE_XL}px; font-weight: 600; color: {Colors.TEXT}; background: transparent;")
        header.addWidget(title)
        header.addStretch()

        # Filter
        filter_label = QLabel("Device:")
        filter_label.setStyleSheet(f"font-size: {Fonts.SIZE_SM}px; color: {Colors.TEXT_DIM}; background: transparent;")
        header.addWidget(filter_label)

        self._device_filter = QComboBox()
        self._device_filter.setFixedWidth(160)
        self._device_filter.addItem("All Devices", "")
        self._device_filter.currentIndexChanged.connect(self._refresh)
        header.addWidget(self._device_filter)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setFixedHeight(30)
        refresh_btn.clicked.connect(self._refresh)
        header.addWidget(refresh_btn)

        export_btn = QPushButton("Export CSV")
        export_btn.setFixedHeight(30)
        export_btn.clicked.connect(self._export_csv)
        header.addWidget(export_btn)

        layout.addLayout(header)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(["Timestamp", "Device", "IP", "Event", "RTT (ms)"])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(0, 170)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(2, 140)
        self._table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(4, 90)
        self._table.setShowGrid(False)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.verticalHeader().setVisible(False)
        self._table.setStyleSheet(f"QTableWidget {{ alternate-background-color: {Colors.BG_ALT}; }}")
        layout.addWidget(self._table, 1)

        # Pagination
        page_row = QHBoxLayout()
        page_row.addStretch()
        self._page_label = QLabel("Page 1")
        self._page_label.setStyleSheet(f"font-size: {Fonts.SIZE_SM}px; color: {Colors.TEXT_DIM}; background: transparent;")
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
        """Update device filter dropdown."""
        current = self._device_filter.currentData()
        self._device_filter.blockSignals(True)
        self._device_filter.clear()
        self._device_filter.addItem("All Devices", "")
        for dev in self._config_service.get_devices():
            self._device_filter.addItem(f"{dev.name} ({dev.ip})", dev.id)
        # Restore selection
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

    def _load_page(self):
        device_id = self._device_filter.currentData() or None
        entries = self._log_service.get_history(
            limit=self._page_size,
            offset=self._page * self._page_size,
            device_id=device_id,
        )

        self._table.setRowCount(0)
        mono = QFont(Fonts.MONO, Fonts.SIZE_SM)

        event_colors = {
            "connected": Colors.CONNECTED,
            "disconnected": Colors.DISCONNECTED,
            "delayed": Colors.DELAYED,
        }

        for entry in entries:
            row = self._table.rowCount()
            self._table.insertRow(row)

            ts_item = QTableWidgetItem(entry.get('timestamp', ''))
            ts_item.setFont(mono)
            self._table.setItem(row, 0, ts_item)

            self._table.setItem(row, 1, QTableWidgetItem(entry.get('device_id', '')))

            ip_item = QTableWidgetItem(entry.get('ip', ''))
            ip_item.setFont(mono)
            self._table.setItem(row, 2, ip_item)

            event = entry.get('event', '')
            event_item = QTableWidgetItem(event.upper())
            color = event_colors.get(event, Colors.TEXT_DIM)
            event_item.setForeground(QColor(color))
            self._table.setItem(row, 3, event_item)

            rtt = entry.get('rtt_ms')
            rtt_item = QTableWidgetItem(f"{rtt:,}" if rtt is not None else "--")
            rtt_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            rtt_item.setFont(mono)
            self._table.setItem(row, 4, rtt_item)

        self._page_label.setText(f"Page {self._page + 1}")
        self._prev_btn.setEnabled(self._page > 0)
        self._next_btn.setEnabled(len(entries) == self._page_size)

    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export History", "history.csv", "CSV Files (*.csv)"
        )
        if not path:
            return

        entries = self._log_service.get_all_entries()
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Device ID", "IP", "Event", "RTT (ms)"])
            for entry in entries:
                writer.writerow([
                    entry.get('timestamp', ''),
                    entry.get('device_id', ''),
                    entry.get('ip', ''),
                    entry.get('event', ''),
                    entry.get('rtt_ms', ''),
                ])
