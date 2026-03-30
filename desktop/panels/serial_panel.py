"""Serial / NMEA Port Monitoring panel."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor

from desktop.theme import Colors, Fonts
from desktop.i18n import t
from backend.services.serial_service import list_serial_ports


class SerialPanel(QWidget):
    monitored_ports_changed = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._monitored_ports = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        self._title_label = QLabel(t("serial.title"))
        self._title_label.setStyleSheet(f"font-size: {Fonts.SIZE_XL}px; font-weight: 600; color: {Colors.TEXT}; background: transparent;")
        layout.addWidget(self._title_label)

        self._guide_label = QLabel(t("guide.serial"))
        self._guide_label.setWordWrap(True)
        self._guide_label.setStyleSheet(
            f"font-size: {Fonts.SIZE_XS}px; color: {Colors.TEXT_MUTED}; background: transparent; padding-bottom: 4px;"
        )
        layout.addWidget(self._guide_label)

        # Controls
        ctrl = QHBoxLayout()
        ctrl.setSpacing(8)

        self._port_input = QLineEdit()
        self._port_input.setPlaceholderText("COM port (e.g. COM3)")
        self._port_input.setFixedWidth(160)
        ctrl.addWidget(self._port_input)

        self._add_btn = QPushButton(t("serial.add_monitor"))
        self._add_btn.setObjectName("btn_primary")
        self._add_btn.setFixedHeight(30)
        self._add_btn.clicked.connect(self._add_port)
        ctrl.addWidget(self._add_btn)

        self._detect_btn = QPushButton(t("serial.detect"))
        self._detect_btn.setFixedHeight(30)
        self._detect_btn.clicked.connect(self._detect_ports)
        ctrl.addWidget(self._detect_btn)

        ctrl.addStretch()

        self._status_label = QLabel("")
        self._status_label.setStyleSheet(f"font-size: {Fonts.SIZE_SM}px; color: {Colors.TEXT_DIM}; background: transparent;")
        ctrl.addWidget(self._status_label)

        layout.addLayout(ctrl)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels([
            t("serial.col_port"), t("serial.col_status"), t("serial.col_desc"),
            t("serial.col_message"), t("serial.col_mfg"),
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(0, 80)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(1, 100)
        self._table.setShowGrid(False)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.verticalHeader().setVisible(False)
        self._table.setStyleSheet(f"QTableWidget {{ alternate-background-color: {Colors.BG_ALT}; }}")
        layout.addWidget(self._table, 1)

        # Initial detection
        self._detect_ports()

    def retranslate(self):
        """Update all translatable strings to the current language."""
        self._title_label.setText(t("serial.title"))
        self._guide_label.setText(t("guide.serial"))
        self._add_btn.setText(t("serial.add_monitor"))
        self._detect_btn.setText(t("serial.detect"))
        self._table.setHorizontalHeaderLabels([
            t("serial.col_port"), t("serial.col_status"), t("serial.col_desc"),
            t("serial.col_message"), t("serial.col_mfg"),
        ])

    def _detect_ports(self):
        ports = list_serial_ports()
        self._table.setRowCount(0)

        if not ports:
            self._status_label.setText(t("serial.no_ports"))
            return

        self._status_label.setText(t("serial.detected", count=len(ports)))

        for p in ports:
            row = self._table.rowCount()
            self._table.insertRow(row)

            port_item = QTableWidgetItem(p['port'])
            self._table.setItem(row, 0, port_item)

            monitored = p['port'] in self._monitored_ports
            status_item = QTableWidgetItem(t("serial.monitored") if monitored else t("serial.available"))
            status_item.setForeground(QColor(Colors.CONNECTED if monitored else Colors.TEXT_DIM))
            self._table.setItem(row, 1, status_item)

            self._table.setItem(row, 2, QTableWidgetItem(p.get('description', '')))
            self._table.setItem(row, 3, QTableWidgetItem("--"))
            self._table.setItem(row, 4, QTableWidgetItem(p.get('manufacturer', '')))

    def _add_port(self):
        port = self._port_input.text().strip().upper()
        if port and port not in self._monitored_ports:
            self._monitored_ports.append(port)
            self._port_input.clear()
            self.monitored_ports_changed.emit(self.get_monitored_ports())
            self._detect_ports()

    def get_monitored_ports(self) -> list:
        return list(self._monitored_ports)

    def update_serial_data(self, results):
        """Update table from serial worker results."""
        self._table.setRowCount(0)

        status_colors = {
            'connected': Colors.CONNECTED,
            'disconnected': Colors.DISCONNECTED,
            'available': Colors.TEXT_DIM,
        }

        for r in results:
            row = self._table.rowCount()
            self._table.insertRow(row)

            port_item = QTableWidgetItem(r.get('port', ''))
            self._table.setItem(row, 0, port_item)

            status = r.get('status', 'available')
            status_item = QTableWidgetItem(status.upper())
            status_item.setForeground(QColor(status_colors.get(status, Colors.TEXT_DIM)))
            self._table.setItem(row, 1, status_item)

            self._table.setItem(row, 2, QTableWidgetItem(r.get('description', '')))
            self._table.setItem(row, 3, QTableWidgetItem(r.get('message', '')))
            self._table.setItem(row, 4, QTableWidgetItem(r.get('manufacturer', '')))

        self._status_label.setText(t("serial.detected", count=len(results)))
