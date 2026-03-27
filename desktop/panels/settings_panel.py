"""Settings panel — monitoring, alerts, profiles, presets."""

import json
import os

import yaml

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QPushButton, QSpinBox, QCheckBox, QGroupBox, QFileDialog,
    QMessageBox, QComboBox, QLineEdit, QScrollArea,
)
from PySide6.QtCore import Qt, Signal

from desktop.theme import Colors, Fonts


class SettingsPanel(QWidget):
    settings_changed = Signal(dict)
    profile_loaded = Signal()     # devices changed
    preset_loaded = Signal()      # devices changed from preset

    def __init__(self, config_service, profile_service, parent=None):
        super().__init__(parent)
        self._config_service = config_service
        self._profile_service = profile_service
        self._build_ui()
        self._load_settings()

    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(16)

        title = QLabel("Settings")
        title.setStyleSheet(f"font-size: {Fonts.SIZE_XL}px; font-weight: 600; color: {Colors.TEXT}; background: transparent;")
        layout.addWidget(title)

        # ── Monitoring ──
        monitor_group = QGroupBox("Monitoring")
        monitor_form = QFormLayout(monitor_group)
        monitor_form.setSpacing(8)

        self._ping_interval = QSpinBox()
        self._ping_interval.setRange(1, 60)
        self._ping_interval.setSuffix(" sec")
        monitor_form.addRow("Ping Interval:", self._ping_interval)

        self._interface_poll = QSpinBox()
        self._interface_poll.setRange(1, 30)
        self._interface_poll.setSuffix(" sec")
        monitor_form.addRow("Interface Poll:", self._interface_poll)

        self._delay_threshold = QSpinBox()
        self._delay_threshold.setRange(10, 5000)
        self._delay_threshold.setSuffix(" ms")
        monitor_form.addRow("Delay Threshold:", self._delay_threshold)

        layout.addWidget(monitor_group)

        # ── Alerts ──
        alert_group = QGroupBox("Alerts")
        alert_form = QFormLayout(alert_group)
        alert_form.setSpacing(8)

        self._alert_enabled = QCheckBox("Enable status change alerts")
        alert_form.addRow(self._alert_enabled)

        self._sound_enabled = QCheckBox("Sound alert on disconnect")
        self._sound_enabled.setChecked(True)
        alert_form.addRow(self._sound_enabled)

        self._escalation_enabled = QCheckBox("Escalation (louder after 3/10 consecutive failures)")
        self._escalation_enabled.setChecked(True)
        alert_form.addRow(self._escalation_enabled)

        layout.addWidget(alert_group)

        # ── Vessel Presets ──
        preset_group = QGroupBox("Vessel Presets")
        preset_layout = QVBoxLayout(preset_group)
        preset_layout.setSpacing(8)

        preset_desc = QLabel("Load a preset device configuration for your vessel type.")
        preset_desc.setStyleSheet(f"font-size: {Fonts.SIZE_SM}px; color: {Colors.TEXT_DIM}; background: transparent;")
        preset_layout.addWidget(preset_desc)

        preset_row = QHBoxLayout()
        self._preset_combo = QComboBox()
        self._preset_combo.setMinimumWidth(250)
        self._refresh_presets()
        preset_row.addWidget(self._preset_combo)

        load_preset_btn = QPushButton("Load Preset")
        load_preset_btn.setObjectName("btn_primary")
        load_preset_btn.setFixedHeight(30)
        load_preset_btn.clicked.connect(self._load_preset)
        preset_row.addWidget(load_preset_btn)

        import_yaml_btn = QPushButton("Import YAML")
        import_yaml_btn.setFixedHeight(30)
        import_yaml_btn.clicked.connect(self._import_preset_yaml)
        preset_row.addWidget(import_yaml_btn)

        preset_row.addStretch()
        preset_layout.addLayout(preset_row)

        layout.addWidget(preset_group)

        # ── Profiles ──
        profile_group = QGroupBox("Project Profiles")
        profile_layout = QVBoxLayout(profile_group)
        profile_layout.setSpacing(8)

        profile_desc = QLabel("Save/load device configurations for different projects or vessels.")
        profile_desc.setStyleSheet(f"font-size: {Fonts.SIZE_SM}px; color: {Colors.TEXT_DIM}; background: transparent;")
        profile_layout.addWidget(profile_desc)

        # Save profile
        save_row = QHBoxLayout()
        save_row.setSpacing(6)

        self._profile_name_input = QLineEdit()
        self._profile_name_input.setPlaceholderText("Profile name (e.g. Orsted Vessel A)")
        self._profile_name_input.setMinimumWidth(200)
        save_row.addWidget(self._profile_name_input)

        self._vessel_input = QLineEdit()
        self._vessel_input.setPlaceholderText("Vessel name (optional)")
        self._vessel_input.setFixedWidth(160)
        save_row.addWidget(self._vessel_input)

        save_profile_btn = QPushButton("Save Current")
        save_profile_btn.setObjectName("btn_primary")
        save_profile_btn.setFixedHeight(30)
        save_profile_btn.clicked.connect(self._save_profile)
        save_row.addWidget(save_profile_btn)

        save_row.addStretch()
        profile_layout.addLayout(save_row)

        # Load profile
        load_row = QHBoxLayout()
        load_row.setSpacing(6)

        self._profile_combo = QComboBox()
        self._profile_combo.setMinimumWidth(250)
        self._refresh_profiles()
        load_row.addWidget(self._profile_combo)

        load_profile_btn = QPushButton("Load")
        load_profile_btn.setFixedHeight(30)
        load_profile_btn.clicked.connect(self._load_profile)
        load_row.addWidget(load_profile_btn)

        del_profile_btn = QPushButton("Delete")
        del_profile_btn.setObjectName("btn_danger")
        del_profile_btn.setFixedHeight(30)
        del_profile_btn.clicked.connect(self._delete_profile)
        load_row.addWidget(del_profile_btn)

        load_row.addStretch()
        profile_layout.addLayout(load_row)

        layout.addWidget(profile_group)

        # ── Config Import/Export ──
        config_group = QGroupBox("Configuration")
        config_layout = QHBoxLayout(config_group)
        config_layout.setSpacing(8)

        import_btn = QPushButton("Import Config")
        import_btn.clicked.connect(self._import_config)
        config_layout.addWidget(import_btn)

        export_btn = QPushButton("Export Config")
        export_btn.clicked.connect(self._export_config)
        config_layout.addWidget(export_btn)

        config_layout.addStretch()
        layout.addWidget(config_group)

        # ── Save button ──
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        save_btn = QPushButton("Save Settings")
        save_btn.setObjectName("btn_primary")
        save_btn.setFixedHeight(34)
        save_btn.clicked.connect(self._save_settings)
        btn_row.addWidget(save_btn)

        layout.addLayout(btn_row)
        layout.addStretch()

        scroll.setWidget(container)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    # ── Settings ──

    def _load_settings(self):
        s = self._config_service.get_settings()
        self._ping_interval.setValue(s.get('ping_interval_seconds', 5))
        self._interface_poll.setValue(s.get('interface_poll_seconds', 3))
        self._delay_threshold.setValue(s.get('delay_threshold_ms', 200))
        self._alert_enabled.setChecked(s.get('alert_enabled', True))
        self._sound_enabled.setChecked(s.get('sound_enabled', True))
        self._escalation_enabled.setChecked(s.get('escalation_enabled', True))

    def _save_settings(self):
        data = {
            'ping_interval_seconds': self._ping_interval.value(),
            'interface_poll_seconds': self._interface_poll.value(),
            'delay_threshold_ms': self._delay_threshold.value(),
            'alert_enabled': self._alert_enabled.isChecked(),
            'sound_enabled': self._sound_enabled.isChecked(),
            'escalation_enabled': self._escalation_enabled.isChecked(),
        }
        self._config_service.update_settings(data)
        self.settings_changed.emit(data)

    def get_alert_settings(self):
        return {
            'alert_enabled': self._alert_enabled.isChecked(),
            'sound_enabled': self._sound_enabled.isChecked(),
            'escalation_enabled': self._escalation_enabled.isChecked(),
        }

    # ── Presets ──

    def _refresh_presets(self):
        self._preset_combo.clear()
        presets_dir = os.path.join(self._config_service._data_dir, 'presets')
        if not os.path.exists(presets_dir):
            return
        for fname in sorted(os.listdir(presets_dir)):
            if fname.endswith(('.yaml', '.yml')):
                path = os.path.join(presets_dir, fname)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                    name = data.get('name', fname)
                    dev_count = len(data.get('devices', []))
                    self._preset_combo.addItem(f"{name} ({dev_count} devices)", path)
                except Exception:
                    self._preset_combo.addItem(fname, path)

    def _load_preset(self):
        path = self._preset_combo.currentData()
        if not path:
            return

        reply = QMessageBox.question(
            self, "Load Preset",
            "This will REPLACE all current devices with the preset. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            devices = data.get('devices', [])
            from backend.models.device import Device

            # Clear existing and add preset devices
            for dev in list(self._config_service.get_devices()):
                self._config_service.delete_device(dev.id)

            for d in devices:
                device = Device.from_dict({
                    'name': d.get('name', ''),
                    'ip': d.get('ip', ''),
                    'ports': d.get('ports', []),
                    'category': d.get('category', 'Other'),
                    'description': d.get('description', ''),
                    'enabled': d.get('enabled', True),
                })
                self._config_service.add_device(device)

            self.preset_loaded.emit()
            QMessageBox.information(
                self, "Preset Loaded",
                f"Loaded {len(devices)} devices from preset."
            )
        except Exception as e:
            QMessageBox.warning(self, "Preset Error", str(e))

    def _import_preset_yaml(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Preset YAML", "", "YAML Files (*.yaml *.yml)"
        )
        if not path:
            return
        # Copy to presets dir
        import shutil
        presets_dir = os.path.join(self._config_service._data_dir, 'presets')
        os.makedirs(presets_dir, exist_ok=True)
        dest = os.path.join(presets_dir, os.path.basename(path))
        shutil.copy2(path, dest)
        self._refresh_presets()
        QMessageBox.information(self, "Import", "Preset YAML imported. Select it from the dropdown.")

    # ── Profiles ──

    def _refresh_profiles(self):
        self._profile_combo.clear()
        for p in self._profile_service.list_profiles():
            label = p['name']
            if p['vessel']:
                label += f" [{p['vessel']}]"
            label += f" ({p['device_count']} dev)"
            self._profile_combo.addItem(label, p['filename'])

    def _save_profile(self):
        name = self._profile_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Save Profile", "Profile name is required.")
            return

        devices = [d.to_dict() for d in self._config_service.get_devices()]
        settings = self._config_service.get_settings()
        vessel = self._vessel_input.text().strip()

        self._profile_service.save_profile(name, devices, settings, vessel=vessel)
        self._refresh_profiles()
        self._profile_name_input.clear()
        self._vessel_input.clear()
        QMessageBox.information(self, "Profile Saved", f"Profile '{name}' saved with {len(devices)} devices.")

    def _load_profile(self):
        filename = self._profile_combo.currentData()
        if not filename:
            return

        reply = QMessageBox.question(
            self, "Load Profile",
            "This will REPLACE current devices and settings. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        profile = self._profile_service.load_profile(filename)
        if not profile:
            QMessageBox.warning(self, "Load Error", "Profile not found.")
            return

        self._config_service.import_config(profile)
        self._load_settings()
        self.profile_loaded.emit()
        QMessageBox.information(self, "Profile Loaded", f"Loaded profile: {profile.get('name', filename)}")

    def _delete_profile(self):
        filename = self._profile_combo.currentData()
        if not filename:
            return
        reply = QMessageBox.question(
            self, "Delete Profile",
            f"Delete profile '{self._profile_combo.currentText()}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._profile_service.delete_profile(filename)
            self._refresh_profiles()

    # ── Config ──

    def _import_config(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Configuration", "", "JSON Files (*.json)"
        )
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self._config_service.import_config(config)
            self._load_settings()
            self.profile_loaded.emit()
            QMessageBox.information(self, "Import", "Configuration imported successfully.")
        except Exception as e:
            QMessageBox.warning(self, "Import Error", str(e))

    def _export_config(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Configuration", "portdetector_config.json", "JSON Files (*.json)"
        )
        if not path:
            return
        try:
            config = self._config_service.export_config()
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            QMessageBox.information(self, "Export", "Configuration exported successfully.")
        except Exception as e:
            QMessageBox.warning(self, "Export Error", str(e))
