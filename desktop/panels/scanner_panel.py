"""Port Scanner panel."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QComboBox, QPushButton, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QProgressBar,
)
from PySide6.QtCore import Qt

from desktop.theme import Colors, Fonts
from desktop.i18n import t
from desktop.workers.scan_worker import ScanWorkerThread


class ScannerPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # Title
        self._title = QLabel(t("scanner.title"))
        self._title.setStyleSheet(f"font-size: {Fonts.SIZE_XL}px; font-weight: 600; color: {Colors.TEXT}; background: transparent;")
        layout.addWidget(self._title)

        self._guide_label = QLabel(t("guide.scanner"))
        self._guide_label.setWordWrap(True)
        self._guide_label.setStyleSheet(
            f"font-size: {Fonts.SIZE_XS}px; color: {Colors.TEXT_MUTED}; background: transparent; padding-bottom: 4px;"
        )
        layout.addWidget(self._guide_label)

        # Form
        form_row = QHBoxLayout()
        form_row.setSpacing(12)

        ip_layout = QVBoxLayout()
        self._ip_label = QLabel(t("scanner.target_ip"))
        self._ip_label.setStyleSheet(f"font-size: {Fonts.SIZE_XS}px; color: {Colors.TEXT_DIM}; background: transparent;")
        ip_layout.addWidget(self._ip_label)
        self._ip_input = QLineEdit()
        self._ip_input.setPlaceholderText("192.168.1.1")
        self._ip_input.setFixedWidth(180)
        ip_layout.addWidget(self._ip_input)
        form_row.addLayout(ip_layout)

        ports_layout = QVBoxLayout()
        self._ports_label = QLabel(t("scanner.ports"))
        self._ports_label.setStyleSheet(f"font-size: {Fonts.SIZE_XS}px; color: {Colors.TEXT_DIM}; background: transparent;")
        ports_layout.addWidget(self._ports_label)
        self._ports_input = QLineEdit()
        self._ports_input.setPlaceholderText("1-1024")
        self._ports_input.setText("1-1024")
        self._ports_input.setFixedWidth(200)
        ports_layout.addWidget(self._ports_input)
        form_row.addLayout(ports_layout)

        proto_layout = QVBoxLayout()
        self._proto_label = QLabel(t("scanner.protocol"))
        self._proto_label.setStyleSheet(f"font-size: {Fonts.SIZE_XS}px; color: {Colors.TEXT_DIM}; background: transparent;")
        proto_layout.addWidget(self._proto_label)
        self._proto_combo = QComboBox()
        self._proto_combo.addItems(["TCP", "UDP"])
        self._proto_combo.setFixedWidth(80)
        proto_layout.addWidget(self._proto_combo)
        form_row.addLayout(proto_layout)

        self._scan_btn = QPushButton(t("scanner.scan"))
        self._scan_btn.setObjectName("btn_primary")
        self._scan_btn.setFixedHeight(32)
        self._scan_btn.clicked.connect(self._start_scan)
        form_row.addWidget(self._scan_btn, 0, Qt.AlignmentFlag.AlignBottom)

        self._stop_btn = QPushButton(t("scanner.stop"))
        self._stop_btn.setObjectName("btn_danger")
        self._stop_btn.setFixedHeight(32)
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self._stop_scan)
        form_row.addWidget(self._stop_btn, 0, Qt.AlignmentFlag.AlignBottom)

        form_row.addStretch()
        layout.addLayout(form_row)

        # Progress
        self._progress = QProgressBar()
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        # Summary
        self._summary_label = QLabel("")
        self._summary_label.setStyleSheet(f"font-size: {Fonts.SIZE_SM}px; color: {Colors.TEXT_DIM}; background: transparent;")
        layout.addWidget(self._summary_label)

        # Results table
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels([
            t("scanner.col_port"), t("scanner.col_protocol"),
            t("scanner.col_state"), t("scanner.col_service"), "IP",
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(0, 80)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(1, 70)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(2, 90)
        self._table.setShowGrid(False)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.verticalHeader().setVisible(False)
        self._table.setStyleSheet(f"""
            QTableWidget {{
                alternate-background-color: {Colors.BG_ALT};
            }}
        """)
        layout.addWidget(self._table, 1)

    def _start_scan(self):
        import re
        ip = self._ip_input.text().strip()
        ports = self._ports_input.text().strip()
        if not ip or not ports:
            return
        if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip):
            self._summary_label.setText(t("scanner.invalid_ip"))
            return

        self._table.setRowCount(0)
        self._scan_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        self._progress.setVisible(True)
        self._progress.setValue(0)
        self._summary_label.setText(t("scanner.scanning"))

        protocol = self._proto_combo.currentText().lower()
        self._worker = ScanWorkerThread(ip, ports, protocol)
        self._worker.progress.connect(self._on_progress)
        self._worker.result.connect(self._on_result)
        self._worker.complete.connect(self._on_complete)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.finished.connect(lambda worker=self._worker: self._clear_worker(worker))
        self._worker.start()

    def _stop_scan(self):
        if self._worker:
            self._worker.stop()
            if hasattr(self._worker, "quit"):
                self._worker.quit()

    def _on_progress(self, data):
        total = data.get('total', 1)
        scanned = data.get('scanned', 0)
        self._progress.setMaximum(total)
        self._progress.setValue(scanned)

    def _on_result(self, data):
        state = data.get('state', '')
        if state not in ('open', 'filtered'):
            return  # Only show open/filtered ports in table

        row = self._table.rowCount()
        self._table.insertRow(row)

        port_item = QTableWidgetItem(str(data.get('port', '')))
        port_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        port_item.setFont(self._mono_font())
        self._table.setItem(row, 0, port_item)

        self._table.setItem(row, 1, QTableWidgetItem(data.get('protocol', '').upper()))

        state_item = QTableWidgetItem(state.upper())
        color = Colors.OPEN if state == "open" else Colors.FILTERED
        state_item.setForeground(pg_color(color))
        self._table.setItem(row, 2, state_item)

        self._table.setItem(row, 3, QTableWidgetItem(data.get('service_name', '')))
        self._table.setItem(row, 4, QTableWidgetItem(data.get('ip', '')))

    def _on_complete(self, data):
        self._scan_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self._progress.setVisible(False)

        open_p = data.get('open_ports', 0)
        closed_p = data.get('closed_ports', 0)
        total_p = data.get('total_ports', 0)
        self._summary_label.setText(
            t("scanner.complete", total=total_p, open=open_p, closed=closed_p)
        )

    def _clear_worker(self, worker):
        if self._worker is worker:
            self._worker = None

    def _mono_font(self):
        from PySide6.QtGui import QFont
        return QFont(Fonts.FAMILY, Fonts.SIZE_SM)

    def set_target_ip(self, ip):
        self._ip_input.setText(ip)

    def set_target(self, ip: str, ports=None):
        self._ip_input.setText(ip)
        if ports:
            self._ports_input.setText(",".join(str(port) for port in ports))
            self._summary_label.setText(
                t("scanner.loaded", ip=ip, ports=", ".join(str(port) for port in ports))
            )
        else:
            self._summary_label.setText(t("scanner.loaded_ip", ip=ip))

    def retranslate(self):
        """Update all translatable strings to current language."""
        self._title.setText(t("scanner.title"))
        self._guide_label.setText(t("guide.scanner"))
        self._ip_label.setText(t("scanner.target_ip"))
        self._ports_label.setText(t("scanner.ports"))
        self._proto_label.setText(t("scanner.protocol"))
        self._scan_btn.setText(t("scanner.scan"))
        self._stop_btn.setText(t("scanner.stop"))
        self._table.setHorizontalHeaderLabels([
            t("scanner.col_port"), t("scanner.col_protocol"),
            t("scanner.col_state"), t("scanner.col_service"), "IP",
        ])


def pg_color(hex_color):
    """Convert hex color to QColor for table items."""
    from PySide6.QtGui import QColor
    return QColor(hex_color)
