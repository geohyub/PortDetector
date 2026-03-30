"""Network Interfaces panel."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor

from desktop.theme import Colors, Fonts
from desktop.i18n import t


def _format_bytes(b):
    """Format bytes to human-readable string."""
    if b < 1024:
        return f"{b:,} B"
    elif b < 1024 * 1024:
        return f"{b / 1024:,.1f} KB"
    elif b < 1024 * 1024 * 1024:
        return f"{b / (1024 * 1024):,.1f} MB"
    else:
        return f"{b / (1024 * 1024 * 1024):,.2f} GB"


def _format_rate(bps):
    """Format bytes/sec to human-readable."""
    if bps < 1024:
        return f"{bps:,.0f} B/s"
    elif bps < 1024 * 1024:
        return f"{bps / 1024:,.1f} KB/s"
    else:
        return f"{bps / (1024 * 1024):,.1f} MB/s"


class InterfacesPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        self._title_label = QLabel(t("interfaces.title"))
        self._title_label.setStyleSheet(f"font-size: {Fonts.SIZE_XL}px; font-weight: 600; color: {Colors.TEXT}; background: transparent;")
        layout.addWidget(self._title_label)

        self._guide_label = QLabel(t("guide.interfaces"))
        self._guide_label.setWordWrap(True)
        self._guide_label.setStyleSheet(
            f"font-size: {Fonts.SIZE_XS}px; color: {Colors.TEXT_MUTED}; background: transparent; padding-bottom: 4px;"
        )
        layout.addWidget(self._guide_label)

        self._table = QTableWidget()
        self._table.setColumnCount(8)
        self._table.setHorizontalHeaderLabels([
            t("interfaces.col_name"), t("interfaces.col_status"), t("interfaces.col_speed"), "IPv4",
            t("interfaces.col_sent"), t("interfaces.col_recv"), t("interfaces.col_tx"), t("interfaces.col_rx"),
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(1, 70)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(2, 80)
        self._table.setShowGrid(False)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.verticalHeader().setVisible(False)
        self._table.setStyleSheet(f"QTableWidget {{ alternate-background-color: {Colors.BG_ALT}; }}")
        layout.addWidget(self._table, 1)

    def retranslate(self):
        """Update all translatable strings to the current language."""
        self._title_label.setText(t("interfaces.title"))
        self._guide_label.setText(t("guide.interfaces"))
        self._table.setHorizontalHeaderLabels([
            t("interfaces.col_name"), t("interfaces.col_status"), t("interfaces.col_speed"), "IPv4",
            t("interfaces.col_sent"), t("interfaces.col_recv"), t("interfaces.col_tx"), t("interfaces.col_rx"),
        ])

    def update_interfaces(self, interfaces):
        """Update table with interface data."""
        self._table.setRowCount(0)

        for iface in interfaces:
            row = self._table.rowCount()
            self._table.insertRow(row)

            # Name
            self._table.setItem(row, 0, QTableWidgetItem(iface.get('name', '')))

            # Status
            is_up = iface.get('is_up', False)
            status_item = QTableWidgetItem("UP" if is_up else "DOWN")
            status_item.setForeground(QColor(Colors.CONNECTED if is_up else Colors.DISCONNECTED))
            self._table.setItem(row, 1, status_item)

            # Speed
            speed = iface.get('speed_mbps', 0)
            speed_item = QTableWidgetItem(f"{speed:,} Mbps" if speed else "--")
            speed_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(row, 2, speed_item)

            # IPv4
            ipv4_item = QTableWidgetItem(iface.get('ipv4') or "--")
            self._table.setItem(row, 3, ipv4_item)

            # Sent/Recv
            for col, key in [(4, 'bytes_sent'), (5, 'bytes_recv')]:
                val = iface.get(key, 0)
                item = QTableWidgetItem(_format_bytes(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self._table.setItem(row, col, item)

            # TX/RX Rate
            for col, key in [(6, 'throughput_out'), (7, 'throughput_in')]:
                val = iface.get(key, 0)
                item = QTableWidgetItem(_format_rate(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self._table.setItem(row, col, item)
