"""Subnet Discovery panel."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from desktop.theme import Colors, Fonts
from desktop.i18n import t
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

        self._title = QLabel(t("discovery.title"))
        self._title.setStyleSheet(f"font-size: {Fonts.SIZE_XL}px; font-weight: 600; color: {Colors.TEXT}; background: transparent;")
        layout.addWidget(self._title)

        self._guide_label = QLabel(t("guide.discovery"))
        self._guide_label.setWordWrap(True)
        self._guide_label.setStyleSheet(
            f"font-size: {Fonts.SIZE_XS}px; color: {Colors.TEXT_MUTED}; background: transparent; padding-bottom: 4px;"
        )
        layout.addWidget(self._guide_label)

        # Subnet input
        row = QHBoxLayout()
        row.setSpacing(8)

        self._sub_label = QLabel(t("discovery.subnet"))
        self._sub_label.setStyleSheet(f"font-size: {Fonts.SIZE_SM}px; color: {Colors.TEXT_DIM}; background: transparent;")
        row.addWidget(self._sub_label)

        self._subnet_input = QLineEdit()
        self._subnet_input.setPlaceholderText("192.168.1")
        self._subnet_input.setFixedWidth(160)
        try:
            self._subnet_input.setText(get_local_subnet())
        except Exception:
            self._subnet_input.setText("192.168.1")
        row.addWidget(self._subnet_input)

        self._discover_btn = QPushButton(t("discovery.discover"))
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
        self._table.setHorizontalHeaderLabels([
            t("discovery.col_ip"), t("discovery.col_rtt"), t("discovery.col_hostname"),
        ])
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
            self._status_label.setText(t("discovery.invalid_subnet"))
            return

        self._table.setRowCount(0)
        self._discover_btn.setEnabled(False)
        self._progress.setVisible(True)
        self._progress.setMaximum(254)
        self._progress.setValue(0)
        self._status_label.setText(t("discovery.scanning"))

        self._worker = DiscoveryWorkerThread(subnet)
        self._worker.progress.connect(self._on_progress)
        self._worker.complete.connect(self._on_complete)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.finished.connect(lambda worker=self._worker: self._clear_worker(worker))
        self._worker.start()

    def _on_progress(self, scanned, total, found_count):
        self._progress.setMaximum(total)
        self._progress.setValue(scanned)
        self._status_label.setText(
            t("discovery.progress", scanned=scanned, total=total, found=found_count)
        )

    def _on_complete(self, results):
        self._discover_btn.setEnabled(True)
        self._progress.setVisible(False)
        self._status_label.setText(t("discovery.complete", count=len(results)))

        for host in results:
            row = self._table.rowCount()
            self._table.insertRow(row)

            ip_item = QTableWidgetItem(host.get('ip', ''))
            self._table.setItem(row, 0, ip_item)

            rtt = host.get('rtt_ms')
            rtt_item = QTableWidgetItem(f"{rtt:,}" if rtt is not None else "--")
            rtt_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(row, 1, rtt_item)

            self._table.setItem(row, 2, QTableWidgetItem(host.get('hostname', '')))

    def _clear_worker(self, worker):
        if self._worker is worker:
            self._worker = None

    def retranslate(self):
        """Update all translatable strings to current language."""
        self._title.setText(t("discovery.title"))
        self._guide_label.setText(t("guide.discovery"))
        self._sub_label.setText(t("discovery.subnet"))
        self._discover_btn.setText(t("discovery.discover"))
        self._table.setHorizontalHeaderLabels([
            t("discovery.col_ip"), t("discovery.col_rtt"), t("discovery.col_hostname"),
        ])
