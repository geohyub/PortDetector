"""Uptime Report panel — device availability statistics + Excel export."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QFileDialog, QMessageBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor

from desktop.theme import Colors, Fonts


class ReportPanel(QWidget):
    def __init__(self, uptime_service, config_service, parent=None):
        super().__init__(parent)
        self._uptime_service = uptime_service
        self._config_service = config_service
        self._report_data = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        title = QLabel("Uptime Report")
        title.setStyleSheet(f"font-size: {Fonts.SIZE_XL}px; font-weight: 600; color: {Colors.TEXT}; background: transparent;")
        layout.addWidget(title)

        # Controls
        ctrl = QHBoxLayout()
        ctrl.setSpacing(8)

        period_label = QLabel("Period:")
        period_label.setStyleSheet(f"font-size: {Fonts.SIZE_SM}px; color: {Colors.TEXT_DIM}; background: transparent;")
        ctrl.addWidget(period_label)

        self._period_combo = QComboBox()
        self._period_combo.addItem("Last 24 hours", 24)
        self._period_combo.addItem("Last 12 hours", 12)
        self._period_combo.addItem("Last 48 hours", 48)
        self._period_combo.addItem("Last 7 days", 168)
        self._period_combo.setFixedWidth(140)
        ctrl.addWidget(self._period_combo)

        gen_btn = QPushButton("Generate")
        gen_btn.setObjectName("btn_primary")
        gen_btn.setFixedHeight(30)
        gen_btn.clicked.connect(self._generate)
        ctrl.addWidget(gen_btn)

        export_btn = QPushButton("Export Excel")
        export_btn.setFixedHeight(30)
        export_btn.clicked.connect(self._export_excel)
        ctrl.addWidget(export_btn)

        ctrl.addStretch()
        layout.addLayout(ctrl)

        # Table
        self._table = QTableWidget()
        cols = ["Device", "IP", "Category", "Uptime %", "Up (min)", "Down (min)",
                "Disconnects", "Avg RTT (ms)", "Status Changes"]
        self._table.setColumnCount(len(cols))
        self._table.setHorizontalHeaderLabels(cols)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        for i in [3, 4, 5, 6, 7, 8]:
            self._table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
            self._table.setColumnWidth(i, 100)
        self._table.setShowGrid(False)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.verticalHeader().setVisible(False)
        self._table.setStyleSheet(f"QTableWidget {{ alternate-background-color: {Colors.BG_ALT}; }}")
        layout.addWidget(self._table, 1)

    def _generate(self):
        hours = self._period_combo.currentData()
        devices = self._config_service.get_devices()
        self._report_data = self._uptime_service.generate_report_data(devices, hours)

        self._table.setRowCount(0)
        mono = QFont(Fonts.MONO, Fonts.SIZE_SM)

        for row_data in self._report_data:
            row = self._table.rowCount()
            self._table.insertRow(row)

            self._table.setItem(row, 0, QTableWidgetItem(row_data['name']))

            ip_item = QTableWidgetItem(row_data['ip'])
            ip_item.setFont(mono)
            self._table.setItem(row, 1, ip_item)

            self._table.setItem(row, 2, QTableWidgetItem(row_data['category']))

            # Uptime %
            pct = row_data['uptime_pct']
            pct_item = QTableWidgetItem(f"{pct:.1f}%")
            pct_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            pct_item.setFont(mono)
            if pct >= 99:
                pct_item.setForeground(QColor(Colors.CONNECTED))
            elif pct >= 95:
                pct_item.setForeground(QColor(Colors.DELAYED))
            else:
                pct_item.setForeground(QColor(Colors.DISCONNECTED))
            self._table.setItem(row, 3, pct_item)

            # Up/Down minutes
            for col, key in [(4, 'up_mins'), (5, 'down_mins')]:
                val = row_data[key]
                item = QTableWidgetItem(f"{val:,.0f}")
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                item.setFont(mono)
                self._table.setItem(row, col, item)

            # Disconnects
            disc = row_data['disconnects']
            disc_item = QTableWidgetItem(str(disc))
            disc_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            disc_item.setFont(mono)
            if disc > 0:
                disc_item.setForeground(QColor(Colors.DISCONNECTED))
            self._table.setItem(row, 6, disc_item)

            # Avg RTT
            avg_rtt = row_data['avg_rtt']
            rtt_text = f"{avg_rtt:,.1f}" if avg_rtt is not None else "--"
            rtt_item = QTableWidgetItem(rtt_text)
            rtt_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            rtt_item.setFont(mono)
            self._table.setItem(row, 7, rtt_item)

            # Status changes
            sc = row_data['status_changes']
            sc_item = QTableWidgetItem(str(sc))
            sc_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            sc_item.setFont(mono)
            self._table.setItem(row, 8, sc_item)

    def _export_excel(self):
        if not self._report_data:
            QMessageBox.information(self, "Export", "Generate a report first.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Export Uptime Report", "uptime_report.xlsx",
            "Excel Files (*.xlsx)"
        )
        if not path:
            return

        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
            from openpyxl.utils import get_column_letter

            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Uptime Report"

            # Header style
            header_font = Font(name="Pretendard", size=11, bold=True, color="FFFFFF")
            header_fill = PatternFill(start_color="0F3460", end_color="0F3460", fill_type="solid")
            thin_border = Border(
                bottom=Side(style='thin', color='2A2A4A'),
            )

            headers = ["Device", "IP", "Category", "Uptime %", "Up (min)",
                        "Down (min)", "Disconnects", "Avg RTT (ms)", "Status Changes"]

            for col, h in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col, value=h)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal='center')

            # Data
            data_font = Font(name="Cascadia Code", size=10)
            num_align = Alignment(horizontal='right')

            for i, row_data in enumerate(self._report_data, 2):
                ws.cell(row=i, column=1, value=row_data['name'])
                ws.cell(row=i, column=2, value=row_data['ip']).font = data_font
                ws.cell(row=i, column=3, value=row_data['category'])

                pct_cell = ws.cell(row=i, column=4, value=row_data['uptime_pct'] / 100)
                pct_cell.number_format = '0.0%'
                pct_cell.alignment = num_align
                pct_cell.font = data_font

                # Conditional color for uptime
                pct = row_data['uptime_pct']
                if pct < 95:
                    pct_cell.font = Font(name="Cascadia Code", size=10, color="EF476F")
                elif pct < 99:
                    pct_cell.font = Font(name="Cascadia Code", size=10, color="FFD166")
                else:
                    pct_cell.font = Font(name="Cascadia Code", size=10, color="06D6A0")

                for col, key in [(5, 'up_mins'), (6, 'down_mins')]:
                    c = ws.cell(row=i, column=col, value=row_data[key])
                    c.number_format = '#,##0'
                    c.alignment = num_align
                    c.font = data_font

                ws.cell(row=i, column=7, value=row_data['disconnects']).alignment = num_align

                avg_rtt = row_data['avg_rtt']
                rtt_cell = ws.cell(row=i, column=8, value=avg_rtt if avg_rtt is not None else '')
                if avg_rtt is not None:
                    rtt_cell.number_format = '#,##0.0'
                rtt_cell.alignment = num_align
                rtt_cell.font = data_font

                ws.cell(row=i, column=9, value=row_data['status_changes']).alignment = num_align

            # Column widths
            widths = [20, 16, 14, 12, 12, 12, 12, 14, 14]
            for col, w in enumerate(widths, 1):
                ws.column_dimensions[get_column_letter(col)].width = w

            wb.save(path)
            QMessageBox.information(self, "Export", f"Report exported to:\n{path}")
        except ImportError:
            QMessageBox.warning(self, "Export Error", "openpyxl is required for Excel export.\npip install openpyxl")
        except Exception as e:
            QMessageBox.warning(self, "Export Error", str(e))
