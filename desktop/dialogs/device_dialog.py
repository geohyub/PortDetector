"""Add/Edit device dialog."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QComboBox, QCheckBox, QLabel, QPushButton,
)
from PySide6.QtCore import Qt

from desktop.theme import Colors, Fonts
from desktop.i18n import t


CATEGORIES = [
    # General
    "System", "Server", "Network", "Storage",
    # Marine Navigation
    "DGNSS", "MRU", "Gyro", "Navigation",
    # Marine Sensors
    "Echo Sounder", "MBES", "SBP", "Sparker", "Streamer",
    "SSS", "SVP", "USBL", "Magnetometer",
    # Marine Systems
    "Acquisition", "Processing",
    # Serial
    "Serial/NMEA",
    # Other
    "Other",
]

IMPORTANCE_OPTIONS = [
    ("Critical", "critical"),
    ("Important", "high"),
    ("Standard", "standard"),
    ("Optional", "optional"),
]


class DeviceDialog(QDialog):
    """Dialog for adding or editing a device."""

    def __init__(self, parent=None, device_data=None):
        super().__init__(parent)
        self._device_data = device_data
        self._is_edit = device_data is not None
        self.setWindowTitle(t("device.edit_title") if self._is_edit else t("device.add_title"))
        self.setFixedWidth(420)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Colors.BG_CARD};
            }}
            QLabel {{
                background: transparent;
                color: {Colors.TEXT_DIM};
                font-size: {Fonts.SIZE_SM}px;
            }}
            #dialog_title {{
                color: {Colors.TEXT};
                font-size: {Fonts.SIZE_LG}px;
                font-weight: 600;
            }}
            #error_label {{
                color: {Colors.DANGER};
                font-size: {Fonts.SIZE_SM}px;
            }}
        """)
        self._build_ui()
        if self._is_edit:
            self._populate(device_data)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 16, 20, 16)

        self._dialog_title = QLabel(t("device.edit_title") if self._is_edit else t("device.add_title"))
        self._dialog_title.setObjectName("dialog_title")
        layout.addWidget(self._dialog_title)

        form = QFormLayout()
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("e.g. GPS Server")
        self._name_label = QLabel(t("device.name"))
        form.addRow(self._name_label, self._name_input)

        self._ip_input = QLineEdit()
        self._ip_input.setPlaceholderText("e.g. 192.168.1.100")
        self._ip_label = QLabel(t("device.ip"))
        form.addRow(self._ip_label, self._ip_input)

        self._ports_input = QLineEdit()
        self._ports_input.setPlaceholderText("e.g. 80,443,8080-8090")
        self._ports_label = QLabel(t("device.ports"))
        form.addRow(self._ports_label, self._ports_input)

        self._category_combo = QComboBox()
        self._category_combo.addItems(CATEGORIES)
        self._category_label = QLabel(t("device.category"))
        form.addRow(self._category_label, self._category_combo)

        self._importance_combo = QComboBox()
        for label, value in IMPORTANCE_OPTIONS:
            self._importance_combo.addItem(label, value)
        self._importance_label = QLabel(t("device.importance"))
        form.addRow(self._importance_label, self._importance_combo)

        self._desc_input = QLineEdit()
        self._desc_input.setPlaceholderText("Optional description")
        self._desc_label = QLabel(t("device.description"))
        form.addRow(self._desc_label, self._desc_input)

        self._enabled_check = QCheckBox(t("device.monitoring_enabled"))
        self._enabled_check.setChecked(True)
        form.addRow("", self._enabled_check)

        layout.addLayout(form)

        self._error_label = QLabel("")
        self._error_label.setObjectName("error_label")
        self._error_label.setVisible(False)
        layout.addWidget(self._error_label)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self._cancel_btn = QPushButton(t("device.cancel"))
        self._cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(self._cancel_btn)

        self._save_btn = QPushButton(t("device.save") if self._is_edit else t("device.add"))
        self._save_btn.setObjectName("btn_primary")
        self._save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(self._save_btn)

        layout.addLayout(btn_row)

    def _populate(self, data):
        self._name_input.setText(data.get('name', ''))
        self._ip_input.setText(data.get('ip', ''))
        ports = data.get('ports', [])
        self._ports_input.setText(','.join(str(p) for p in ports))
        cat = data.get('category', 'Other')
        idx = self._category_combo.findText(cat)
        if idx >= 0:
            self._category_combo.setCurrentIndex(idx)
        importance = data.get('importance', 'standard')
        idx = self._importance_combo.findData(importance)
        if idx >= 0:
            self._importance_combo.setCurrentIndex(idx)
        self._desc_input.setText(data.get('description', ''))
        self._enabled_check.setChecked(data.get('enabled', True))

    def _on_save(self):
        name = self._name_input.text().strip()
        ip = self._ip_input.text().strip()
        ports_str = self._ports_input.text().strip()

        if not name:
            self._show_error(t("device.name_required"))
            return
        if not ip:
            self._show_error(t("device.ip_required"))
            return

        # Parse ports
        ports = []
        if ports_str:
            from backend.services.scan_service import parse_port_range
            ports = parse_port_range(ports_str)

        self._result = {
            'name': name,
            'ip': ip,
            'ports': ports,
            'category': self._category_combo.currentText(),
            'importance': self._importance_combo.currentData(),
            'description': self._desc_input.text().strip(),
            'enabled': self._enabled_check.isChecked(),
        }
        self.accept()

    def _show_error(self, msg):
        self._error_label.setText(msg)
        self._error_label.setVisible(True)

    def get_result(self):
        return getattr(self, '_result', None)
