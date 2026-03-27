"""Subnet Discovery panel."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from desktop.theme import Colors, Fonts
from desktop.workers.discovery_worker import DiscoveryWorkerThread
from backend.services.discovery_service import get_local_subnet


class DiscoveryPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        title = QLabel("Subnet Discovery")
        title.setStyleSheet(f"font-size: {Fonts.SIZE_XL}px; font-weight: 600; color: {Colors.TEXT}; background: transparent;")
        layout.addWidget(title)

        # Subnet input
        row = QHBoxLayout()
        row.setSpacing(8)

        sub_label = QLabel("Subnet:")
        sub_label.setStyleSheet(f"font-size: {Fonts.SIZE_SM}px; color: {Colors.TEXT_DIM}; background: transparent;")
        row.addWidget(sub_label)

        self._subnet_input = QLineEdit()
        self._subnet_input.setPlaceholderText("192.168.1")
        self._subnet_input.setFixedWidth(160)
        try:
            self._subnet_input.setText(get_local_subnet())
        except Exception:
            self._subnet_input.setText("192.168.1")
        row.addWidget(self._subnet_input)

        self._discover_btn = QPushButton("Discover")
        self._discover_btn.setObjectName("btn_primary")
        self._discover_btn.setFixedHeight(32)
        self._discover_btn.clicked.connect(self._start_discovery)
        row.addWidget(self._discover_btn)

        row.addStretch()
        layout.addLayout(row)

        # Progress
        self._progress = QProgressBar()
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        self._status_label = QLabel("")
        self._status_label.setStyleSheet(f"font-size: {Fonts.SIZE_SM}px; color: {Colors.TEXT_DIM}; background: transparent;")
        layout.addWidget(self._status_label)

        # Results table
        self._table = QTableWidget()
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels(["IP Address", "RTT (ms)", "Hostname"])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(0, 160)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(1, 100)
        self._table.setShowGrid(False)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.verticalHeader().setVisible(False)
        self._table.setStyleSheet(f"QTableWidget {{ alternate-background-color: {Colors.BG_ALT}; }}")
        layout.addWidget(self._table, 1)

    def _start_discovery(self):
        import re
        subnet = self._subnet_input.text().strip()
        if not subnet:
            return
        if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}$', subnet):
            self._status_label.setText("Invalid subnet format (e.g. 192.168.1)")
            return

        self._table.setRowCount(0)
        self._discover_btn.setEnabled(False)
        self._progress.setVisible(True)
        self._progress.setMaximum(254)
        self._progress.setValue(0)
        self._status_label.setText("Scanning subnet...")

        self._worker = DiscoveryWorkerThread(subnet)
        self._worker.progress.connect(self._on_progress)
        self._worker.complete.connect(self._on_complete)
        self._worker.start()

    def _on_progress(self, scanned, total, found_count):
        self._progress.setMaximum(total)
        self._progress.setValue(scanned)
        self._status_label.setText(f"Scanned {scanned}/{total} — Found {found_count} hosts")

    def _on_complete(self, results):
        self._discover_btn.setEnabled(True)
        self._progress.setVisible(False)
        self._status_label.setText(f"Discovery complete: {len(results)} active hosts found")
        self._worker = None

        mono = QFont(Fonts.MONO, Fonts.SIZE_SM)

        for host in results:
            row = self._table.rowCount()
            self._table.insertRow(row)

            ip_item = QTableWidgetItem(host.get('ip', ''))
            ip_item.setFont(mono)
            self._table.setItem(row, 0, ip_item)

            rtt = host.get('rtt_ms')
            rtt_item = QTableWidgetItem(f"{rtt:,}" if rtt is not None else "--")
            rtt_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            rtt_item.setFont(mono)
            self._table.setItem(row, 1, rtt_item)

            self._table.setItem(row, 2, QTableWidgetItem(host.get('hostname', '')))
