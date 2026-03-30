"""Traceroute panel."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from desktop.theme import Colors, Fonts
from desktop.i18n import t
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

        self._title = QLabel(t("traceroute.title"))
        self._title.setStyleSheet(f"font-size: {Fonts.SIZE_XL}px; font-weight: 600; color: {Colors.TEXT}; background: transparent;")
        layout.addWidget(self._title)

        self._guide_label = QLabel(t("guide.traceroute"))
        self._guide_label.setWordWrap(True)
        self._guide_label.setStyleSheet(
            f"font-size: {Fonts.SIZE_XS}px; color: {Colors.TEXT_MUTED}; background: transparent; padding-bottom: 4px;"
        )
        layout.addWidget(self._guide_label)

        row = QHBoxLayout()
        row.setSpacing(8)

        self._target_label = QLabel(t("traceroute.target"))
        self._target_label.setStyleSheet(f"font-size: {Fonts.SIZE_SM}px; color: {Colors.TEXT_DIM}; background: transparent;")
        row.addWidget(self._target_label)

        self._ip_input = QLineEdit()
        self._ip_input.setPlaceholderText("8.8.8.8")
        self._ip_input.setFixedWidth(180)
        row.addWidget(self._ip_input)

        self._trace_btn = QPushButton(t("traceroute.trace"))
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
        self._table.setHorizontalHeaderLabels([
            t("traceroute.col_hop"), "IP", "RTT 1 (ms)", "RTT 2 (ms)", "RTT 3 (ms)", "Avg (ms)",
        ])
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
        self._status_label.setText(t("traceroute.tracing"))

        self._worker = TracerouteWorkerThread(ip)
        self._worker.complete.connect(self._on_complete)
        self._worker.start()

    def _on_complete(self, hops):
        self._trace_btn.setEnabled(True)
        self._status_label.setText(t("traceroute.complete", count=len(hops)))
        self._worker = None

        for hop in hops:
            row = self._table.rowCount()
            self._table.insertRow(row)

            hop_item = QTableWidgetItem(str(hop.get('hop', '')))
            hop_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 0, hop_item)

            ip_item = QTableWidgetItem(hop.get('ip', '*'))
            self._table.setItem(row, 1, ip_item)

            for col, key in enumerate(['rtt1', 'rtt2', 'rtt3', 'avg_rtt'], start=2):
                val = hop.get(key)
                text = f"{val:,}" if val is not None else "*"
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                if val is not None and val > 100:
                    from PySide6.QtGui import QColor
                    item.setForeground(QColor(Colors.WARNING))
                self._table.setItem(row, col, item)

    def retranslate(self):
        """Update all translatable strings to current language."""
        self._title.setText(t("traceroute.title"))
        self._guide_label.setText(t("guide.traceroute"))
        self._target_label.setText(t("traceroute.target"))
        self._trace_btn.setText(t("traceroute.trace"))
        self._table.setHorizontalHeaderLabels([
            t("traceroute.col_hop"), "IP", "RTT 1 (ms)", "RTT 2 (ms)", "RTT 3 (ms)", "Avg (ms)",
        ])
