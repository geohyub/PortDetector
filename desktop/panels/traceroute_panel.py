"""Traceroute panel."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from desktop.theme import Colors, Fonts
from desktop.workers.traceroute_worker import TracerouteWorkerThread


class TraceroutePanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        title = QLabel("Traceroute")
        title.setStyleSheet(f"font-size: {Fonts.SIZE_XL}px; font-weight: 600; color: {Colors.TEXT}; background: transparent;")
        layout.addWidget(title)

        row = QHBoxLayout()
        row.setSpacing(8)

        ip_label = QLabel("Target:")
        ip_label.setStyleSheet(f"font-size: {Fonts.SIZE_SM}px; color: {Colors.TEXT_DIM}; background: transparent;")
        row.addWidget(ip_label)

        self._ip_input = QLineEdit()
        self._ip_input.setPlaceholderText("8.8.8.8")
        self._ip_input.setFixedWidth(180)
        row.addWidget(self._ip_input)

        self._trace_btn = QPushButton("Trace")
        self._trace_btn.setObjectName("btn_primary")
        self._trace_btn.setFixedHeight(32)
        self._trace_btn.clicked.connect(self._start_trace)
        row.addWidget(self._trace_btn)

        row.addStretch()

        self._status_label = QLabel("")
        self._status_label.setStyleSheet(f"font-size: {Fonts.SIZE_SM}px; color: {Colors.TEXT_DIM}; background: transparent;")
        row.addWidget(self._status_label)

        layout.addLayout(row)

        # Hops table
        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels(["Hop", "IP", "RTT 1 (ms)", "RTT 2 (ms)", "RTT 3 (ms)", "Avg (ms)"])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(0, 50)
        for col in range(2, 6):
            self._table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.Fixed)
            self._table.setColumnWidth(col, 90)
        self._table.setShowGrid(False)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.verticalHeader().setVisible(False)
        self._table.setStyleSheet(f"QTableWidget {{ alternate-background-color: {Colors.BG_ALT}; }}")
        layout.addWidget(self._table, 1)

    def _start_trace(self):
        ip = self._ip_input.text().strip()
        if not ip:
            return

        self._table.setRowCount(0)
        self._trace_btn.setEnabled(False)
        self._status_label.setText("Tracing route...")

        self._worker = TracerouteWorkerThread(ip)
        self._worker.complete.connect(self._on_complete)
        self._worker.start()

    def _on_complete(self, hops):
        self._trace_btn.setEnabled(True)
        self._status_label.setText(f"Complete: {len(hops)} hops")
        self._worker = None

        mono = QFont(Fonts.MONO, Fonts.SIZE_SM)

        for hop in hops:
            row = self._table.rowCount()
            self._table.insertRow(row)

            hop_item = QTableWidgetItem(str(hop.get('hop', '')))
            hop_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 0, hop_item)

            ip_item = QTableWidgetItem(hop.get('ip', '*'))
            ip_item.setFont(mono)
            self._table.setItem(row, 1, ip_item)

            for col, key in enumerate(['rtt1', 'rtt2', 'rtt3', 'avg_rtt'], start=2):
                val = hop.get(key)
                text = f"{val:,}" if val is not None else "*"
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                item.setFont(mono)
                if val is not None and val > 100:
                    from PySide6.QtGui import QColor
                    item.setForeground(QColor(Colors.WARNING))
                self._table.setItem(row, col, item)
