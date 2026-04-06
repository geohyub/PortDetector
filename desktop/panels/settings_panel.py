"""Settings panel — monitoring, alerts, profiles, presets."""

import json
import os

import yaml

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QPushButton, QSpinBox, QCheckBox, QGroupBox, QFileDialog, QComboBox, QLineEdit, QScrollArea,
)
from PySide6.QtCore import Qt, Signal

from desktop.theme import Colors, Fonts
from desktop.i18n import t, get_language


class SettingsPanel(QWidget):
    settings_changed = Signal(dict)
    profile_loaded = Signal()     # devices changed
    preset_loaded = Signal()      # devices changed from preset
    language_changed = Signal(str)

    def __init__(self, config_service, profile_service, backup_service, parent=None):
        super().__init__(parent)
        self._config_service = config_service
        self._profile_service = profile_service
        self._backup_service = backup_service
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

        self._title = QLabel(t("settings.title"))
        self._title.setStyleSheet(f"font-size: {Fonts.SIZE_XL}px; font-weight: 600; color: {Colors.TEXT}; background: transparent;")
        layout.addWidget(self._title)

        self._guide_label = QLabel(t("guide.settings"))
        self._guide_label.setWordWrap(True)
        self._guide_label.setStyleSheet(
            f"font-size: {Fonts.SIZE_XS}px; color: {Colors.TEXT_MUTED}; background: transparent; padding-bottom: 4px;"
        )
        layout.addWidget(self._guide_label)

        # ── Language ──
        self._lang_group = QGroupBox(t("settings.language"))
        lang_layout = QHBoxLayout(self._lang_group)
        self._lang_combo = QComboBox()
        self._lang_combo.addItem(t("settings.lang_ko"), "ko")
        self._lang_combo.addItem(t("settings.lang_en"), "en")
        current_lang = get_language()
        idx = self._lang_combo.findData(current_lang)
        if idx >= 0:
            self._lang_combo.setCurrentIndex(idx)
        self._lang_combo.currentIndexChanged.connect(self._on_language_changed)
        lang_layout.addWidget(self._lang_combo)
        lang_layout.addStretch()
        layout.addWidget(self._lang_group)

        # ── Monitoring ──
        self._monitor_group = QGroupBox(t("settings.monitoring"))
        monitor_form = QFormLayout(self._monitor_group)
        monitor_form.setSpacing(8)

        self._ping_interval = QSpinBox()
        self._ping_interval.setRange(1, 60)
        self._ping_interval.setSuffix(" sec")
        self._ping_interval_label = QLabel(t("settings.ping_interval"))
        monitor_form.addRow(self._ping_interval_label, self._ping_interval)

        self._interface_poll = QSpinBox()
        self._interface_poll.setRange(1, 30)
        self._interface_poll.setSuffix(" sec")
        self._interface_poll_label = QLabel(t("settings.interface_poll"))
        monitor_form.addRow(self._interface_poll_label, self._interface_poll)

        self._delay_threshold = QSpinBox()
        self._delay_threshold.setRange(10, 5000)
        self._delay_threshold.setSuffix(" ms")
        self._delay_threshold_label = QLabel(t("settings.delay_threshold"))
        monitor_form.addRow(self._delay_threshold_label, self._delay_threshold)

        layout.addWidget(self._monitor_group)

        # ── Alerts ──
        self._alert_group = QGroupBox(t("settings.alerts"))
        alert_form = QFormLayout(self._alert_group)
        alert_form.setSpacing(8)

        self._alert_enabled = QCheckBox(t("settings.alert_enabled"))
        alert_form.addRow(self._alert_enabled)

        self._sound_enabled = QCheckBox(t("settings.sound_enabled"))
        self._sound_enabled.setChecked(True)
        alert_form.addRow(self._sound_enabled)

        self._escalation_enabled = QCheckBox(t("settings.escalation"))
        self._escalation_enabled.setChecked(True)
        alert_form.addRow(self._escalation_enabled)

        layout.addWidget(self._alert_group)

        # ── Vessel Presets ──
        self._preset_group = QGroupBox(t("settings.vessel_presets"))
        preset_layout = QVBoxLayout(self._preset_group)
        preset_layout.setSpacing(8)

        self._preset_desc = QLabel(t("settings.preset_desc"))
        self._preset_desc.setStyleSheet(f"font-size: {Fonts.SIZE_SM}px; color: {Colors.TEXT_DIM}; background: transparent;")
        preset_layout.addWidget(self._preset_desc)

        preset_row = QHBoxLayout()
        self._preset_combo = QComboBox()
        self._preset_combo.setMinimumWidth(250)
        self._refresh_presets()
        preset_row.addWidget(self._preset_combo)

        self._load_preset_btn = QPushButton(t("settings.load_preset"))
        self._load_preset_btn.setObjectName("btn_primary")
        self._load_preset_btn.setFixedHeight(30)
        self._load_preset_btn.clicked.connect(self._load_preset)
        preset_row.addWidget(self._load_preset_btn)

        self._import_yaml_btn = QPushButton(t("settings.import_yaml"))
        self._import_yaml_btn.setFixedHeight(30)
        self._import_yaml_btn.clicked.connect(self._import_preset_yaml)
        preset_row.addWidget(self._import_yaml_btn)

        preset_row.addStretch()
        preset_layout.addLayout(preset_row)

        layout.addWidget(self._preset_group)

        # ── Profiles ──
        self._profile_group = QGroupBox(t("settings.profiles"))
        profile_layout = QVBoxLayout(self._profile_group)
        profile_layout.setSpacing(8)

        self._profile_desc = QLabel(t("settings.profile_desc"))
        self._profile_desc.setStyleSheet(f"font-size: {Fonts.SIZE_SM}px; color: {Colors.TEXT_DIM}; background: transparent;")
        profile_layout.addWidget(self._profile_desc)

        # Save profile
        save_row = QHBoxLayout()
        save_row.setSpacing(6)

        self._profile_name_input = QLineEdit()
        self._profile_name_input.setPlaceholderText(t("settings.profile_name"))
        self._profile_name_input.setMinimumWidth(200)
        save_row.addWidget(self._profile_name_input)

        self._vessel_input = QLineEdit()
        self._vessel_input.setPlaceholderText(t("settings.vessel_name"))
        self._vessel_input.setFixedWidth(160)
        save_row.addWidget(self._vessel_input)

        self._save_profile_btn = QPushButton(t("settings.save_current"))
        self._save_profile_btn.setObjectName("btn_primary")
        self._save_profile_btn.setFixedHeight(30)
        self._save_profile_btn.clicked.connect(self._save_profile)
        save_row.addWidget(self._save_profile_btn)

        save_row.addStretch()
        profile_layout.addLayout(save_row)

        # Load profile
        load_row = QHBoxLayout()
        load_row.setSpacing(6)

        self._profile_combo = QComboBox()
        self._profile_combo.setMinimumWidth(250)
        self._refresh_profiles()
        load_row.addWidget(self._profile_combo)

        self._load_profile_btn = QPushButton(t("settings.load"))
        self._load_profile_btn.setFixedHeight(30)
        self._load_profile_btn.clicked.connect(self._load_profile)
        load_row.addWidget(self._load_profile_btn)

        self._del_profile_btn = QPushButton(t("settings.delete"))
        self._del_profile_btn.setObjectName("btn_danger")
        self._del_profile_btn.setFixedHeight(30)
        self._del_profile_btn.clicked.connect(self._delete_profile)
        load_row.addWidget(self._del_profile_btn)

        load_row.addStretch()
        profile_layout.addLayout(load_row)

        layout.addWidget(self._profile_group)

        # ── Safety Backups ──
        self._backup_group = QGroupBox(t("settings.safety_backups"))
        backup_layout = QVBoxLayout(self._backup_group)
        backup_layout.setSpacing(8)

        self._backup_desc = QLabel(t("settings.backup_desc"))
        self._backup_desc.setWordWrap(True)
        self._backup_desc.setStyleSheet(f"font-size: {Fonts.SIZE_SM}px; color: {Colors.TEXT_DIM}; background: transparent;")
        backup_layout.addWidget(self._backup_desc)

        self._backup_status = QLabel("")
        self._backup_status.setWordWrap(True)
        self._backup_status.setStyleSheet(f"font-size: {Fonts.SIZE_XS}px; color: {Colors.TEXT_MUTED}; background: transparent;")
        backup_layout.addWidget(self._backup_status)

        backup_row = QHBoxLayout()
        backup_row.setSpacing(6)

        self._backup_combo = QComboBox()
        self._backup_combo.setMinimumWidth(320)
        backup_row.addWidget(self._backup_combo)

        self._refresh_backup_btn = QPushButton(t("settings.refresh"))
        self._refresh_backup_btn.setFixedHeight(30)
        self._refresh_backup_btn.clicked.connect(self._refresh_backups)
        backup_row.addWidget(self._refresh_backup_btn)

        self._create_backup_btn = QPushButton(t("settings.create_backup"))
        self._create_backup_btn.setFixedHeight(30)
        self._create_backup_btn.clicked.connect(self._create_manual_backup)
        backup_row.addWidget(self._create_backup_btn)

        self._restore_backup_btn = QPushButton(t("settings.restore"))
        self._restore_backup_btn.setObjectName("btn_primary")
        self._restore_backup_btn.setFixedHeight(30)
        self._restore_backup_btn.clicked.connect(self._restore_backup)
        backup_row.addWidget(self._restore_backup_btn)

        backup_row.addStretch()
        backup_layout.addLayout(backup_row)
        layout.addWidget(self._backup_group)

        # ── Config Import/Export ──
        self._config_group = QGroupBox(t("settings.configuration"))
        config_layout = QHBoxLayout(self._config_group)
        config_layout.setSpacing(8)

        self._import_btn = QPushButton(t("settings.import_config"))
        self._import_btn.clicked.connect(self._import_config)
        config_layout.addWidget(self._import_btn)

        self._export_btn = QPushButton(t("settings.export_config"))
        self._export_btn.clicked.connect(self._export_config)
        config_layout.addWidget(self._export_btn)

        config_layout.addStretch()
        layout.addWidget(self._config_group)

        # ── Save button ──
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self._save_btn = QPushButton(t("settings.save_settings"))
        self._save_btn.setObjectName("btn_primary")
        self._save_btn.setFixedHeight(34)
        self._save_btn.clicked.connect(self._save_settings)
        btn_row.addWidget(self._save_btn)

        layout.addLayout(btn_row)
        layout.addStretch()

        scroll.setWidget(container)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        self._refresh_backups()

    # ── Language ──

    def _on_language_changed(self):
        self.language_changed.emit(self._lang_combo.currentData())

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

    # ── Backups ──

    def _refresh_backups(self, select_filename=None):
        current = select_filename or self._backup_combo.currentData()
        backups = self._backup_service.list_backups()

        self._backup_combo.blockSignals(True)
        self._backup_combo.clear()
        self._backup_combo.addItem(t("settings.select_backup"), "")
        for backup in backups:
            label = f"{backup['created']} | {backup['source']} ({backup['device_count']} dev)"
            self._backup_combo.addItem(label, backup['filename'])
        self._backup_combo.blockSignals(False)

        for i in range(self._backup_combo.count()):
            if self._backup_combo.itemData(i) == current:
                self._backup_combo.setCurrentIndex(i)
                break

        if backups:
            latest = backups[0]
            self._backup_status.setText(
                f"Latest backup: {latest['created']} | {latest['source']} | "
                f"{latest['device_count']} device(s)"
            )
        else:
            self._backup_status.setText(t("common.no_backup"))

    def _create_restore_point(self, source: str, note: str):
        backup = self._backup_service.create_backup(
            self._config_service.export_config(),
            source=source,
            note=note,
        )
        self._refresh_backups(select_filename=backup['filename'])
        return backup

    def _create_manual_backup(self):
        try:
            backup = self._create_restore_point(
                "manual-backup",
                "Manual backup created from Settings.",
            )
            from geoview_pyside6.widgets.confirm_dialog import ConfirmDialog

            ConfirmDialog(
                "Backup Created",
                f"Saved backup:\n{backup['filename']}",
                confirm_text="OK",
                cancel_text="",
                dialog_type="success",
                parent=self,
            ).exec()
        except Exception as e:
            from geoview_pyside6.widgets.confirm_dialog import ConfirmDialog

            ConfirmDialog("Backup Error", str(e), confirm_text="OK", cancel_text="", dialog_type="warning", parent=self).exec()
    def _restore_backup(self):
        filename = self._backup_combo.currentData()
        if not filename:
            from geoview_pyside6.widgets.confirm_dialog import ConfirmDialog

            ConfirmDialog("Restore Backup", "Select a backup first.", confirm_text="OK", cancel_text="", dialog_type="success", parent=self).exec()
            return

        from geoview_pyside6.widgets.confirm_dialog import ConfirmDialog


        _cdlg = ConfirmDialog(
            "Restore Backup",
            "This will REPLACE the current devices and settings with the selected backup. Continue?",
            confirm_text="Yes",
            cancel_text="No",
            dialog_type="warning",
            parent=self,
        )
        if _cdlg.exec() != _cdlg.Accepted:
            return

        try:
            restore_point = self._create_restore_point(
                "before-backup-restore",
                f"Automatic restore point before restoring {filename}",
            )
            payload = self._backup_service.restore_backup(filename)
            if not payload:
                raise ValueError("Backup not found.")

            self._config_service.import_config(payload["config"])
            self._load_settings()
            self.profile_loaded.emit()
            from geoview_pyside6.widgets.confirm_dialog import ConfirmDialog

            ConfirmDialog(
                "Backup Restored",
                f"Restored backup '{filename}'.\n"
                f"Previous state was saved as '{restore_point['filename']}'.",
                confirm_text="OK",
                cancel_text="",
                dialog_type="success",
                parent=self,
            ).exec()
        except Exception as e:
            from geoview_pyside6.widgets.confirm_dialog import ConfirmDialog

            ConfirmDialog("Restore Error", str(e), confirm_text="OK", cancel_text="", dialog_type="warning", parent=self).exec()
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

        from geoview_pyside6.widgets.confirm_dialog import ConfirmDialog


        _cdlg = ConfirmDialog(
            "Load Preset",
            "This will REPLACE all current devices with the preset. Continue?",
            confirm_text="Yes",
            cancel_text="No",
            dialog_type="warning",
            parent=self,
        )
        if _cdlg.exec() != _cdlg.Accepted:
            return

        try:
            restore_point = self._create_restore_point(
                "before-load-preset",
                f"Automatic restore point before preset {os.path.basename(path)}",
            )
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            devices = data.get('devices', [])
            from backend.models.device import Device
            imported_devices = []
            for d in devices:
                device = Device.from_dict({
                    'name': d.get('name', ''),
                    'ip': d.get('ip', ''),
                    'ports': d.get('ports', []),
                    'category': d.get('category', 'Other'),
                    'importance': d.get('importance', 'standard'),
                    'description': d.get('description', ''),
                    'enabled': d.get('enabled', True),
                })
                errors = device.validate()
                if errors:
                    raise ValueError("; ".join(errors))
                imported_devices.append(device.to_dict())

            config = self._config_service.export_config()
            config['devices'] = imported_devices
            self._config_service.import_config(config)

            self.preset_loaded.emit()
            from geoview_pyside6.widgets.confirm_dialog import ConfirmDialog

            ConfirmDialog(
                "Preset Loaded",
                f"Loaded {len(devices)} devices from preset.\n"
                f"Backup created: {restore_point['filename']}",
                confirm_text="OK",
                cancel_text="",
                dialog_type="success",
                parent=self,
            ).exec()
        except Exception as e:
            from geoview_pyside6.widgets.confirm_dialog import ConfirmDialog

            ConfirmDialog("Preset Error", str(e), confirm_text="OK", cancel_text="", dialog_type="warning", parent=self).exec()
    def _import_preset_yaml(self):
        path, _ = QFileDialog.getOpenFileName(
            self, t("settings.import_yaml"), "", "YAML Files (*.yaml *.yml)"
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
        from geoview_pyside6.widgets.confirm_dialog import ConfirmDialog

        ConfirmDialog(t("common.import"), "Preset YAML imported. Select it from the dropdown.", confirm_text="OK", cancel_text="", dialog_type="success", parent=self).exec()
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
            from geoview_pyside6.widgets.confirm_dialog import ConfirmDialog

            ConfirmDialog("Save Profile", "Profile name is required.", confirm_text="OK", cancel_text="", dialog_type="warning", parent=self).exec()
            return

        devices = [d.to_dict() for d in self._config_service.get_devices()]
        settings = self._config_service.get_settings()
        vessel = self._vessel_input.text().strip()

        self._profile_service.save_profile(name, devices, settings, vessel=vessel)
        self._refresh_profiles()
        self._profile_name_input.clear()
        self._vessel_input.clear()
        from geoview_pyside6.widgets.confirm_dialog import ConfirmDialog

        ConfirmDialog("Profile Saved", f"Profile '{name}' saved with {len(devices)} devices.", confirm_text="OK", cancel_text="", dialog_type="success", parent=self).exec()
    def _load_profile(self):
        filename = self._profile_combo.currentData()
        if not filename:
            return

        from geoview_pyside6.widgets.confirm_dialog import ConfirmDialog


        _cdlg = ConfirmDialog(
            "Load Profile",
            "This will REPLACE current devices and settings. Continue?",
            confirm_text="Yes",
            cancel_text="No",
            dialog_type="warning",
            parent=self,
        )
        if _cdlg.exec() != _cdlg.Accepted:
            return

        try:
            restore_point = self._create_restore_point(
                "before-load-profile",
                f"Automatic restore point before profile {filename}",
            )
            profile = self._profile_service.load_profile(filename)
            if not profile:
                from geoview_pyside6.widgets.confirm_dialog import ConfirmDialog

                ConfirmDialog("Load Error", "Profile not found.", confirm_text="OK", cancel_text="", dialog_type="warning", parent=self).exec()
                return

            self._config_service.import_config(profile)
            self._load_settings()
            self.profile_loaded.emit()
            from geoview_pyside6.widgets.confirm_dialog import ConfirmDialog

            ConfirmDialog(
                "Profile Loaded",
                f"Loaded profile: {profile.get('name', filename)}\n"
                f"Backup created: {restore_point['filename']}",
                confirm_text="OK",
                cancel_text="",
                dialog_type="success",
                parent=self,
            ).exec()
        except Exception as e:
            from geoview_pyside6.widgets.confirm_dialog import ConfirmDialog

            ConfirmDialog("Load Error", str(e), confirm_text="OK", cancel_text="", dialog_type="warning", parent=self).exec()
    def _delete_profile(self):
        filename = self._profile_combo.currentData()
        if not filename:
            return
        from geoview_pyside6.widgets.confirm_dialog import ConfirmDialog

        _cdlg = ConfirmDialog(
            "Delete Profile",
            f"Delete profile '{self._profile_combo.currentText()}'?",
            confirm_text="Yes",
            cancel_text="No",
            dialog_type="warning",
            parent=self,
        )
        if _cdlg.exec() == _cdlg.Accepted:
            self._profile_service.delete_profile(filename)
            self._refresh_profiles()

    # ── Config ──

    def _import_config(self):
        path, _ = QFileDialog.getOpenFileName(
            self, t("settings.import_config"), "", "JSON Files (*.json)"
        )
        if not path:
            return
        try:
            restore_point = self._create_restore_point(
                "before-import-config",
                f"Automatic restore point before importing {os.path.basename(path)}",
            )
            with open(path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self._config_service.import_config(config)
            self._load_settings()
            self.profile_loaded.emit()
            from geoview_pyside6.widgets.confirm_dialog import ConfirmDialog

            ConfirmDialog(
                t("common.import"),
                "Configuration imported successfully.\n"
                f"Backup created: {restore_point['filename']}",
                confirm_text="OK",
                cancel_text="",
                dialog_type="success",
                parent=self,
            ).exec()
        except Exception as e:
            from geoview_pyside6.widgets.confirm_dialog import ConfirmDialog

            ConfirmDialog(t("common.error"), str(e), confirm_text="OK", cancel_text="", dialog_type="warning", parent=self).exec()
    def _export_config(self):
        path, _ = QFileDialog.getSaveFileName(
            self, t("settings.export_config"), "portdetector_config.json", "JSON Files (*.json)"
        )
        if not path:
            return
        try:
            config = self._config_service.export_config()
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            from geoview_pyside6.widgets.confirm_dialog import ConfirmDialog

            ConfirmDialog(t("common.export"), "Configuration exported successfully.", confirm_text="OK", cancel_text="", dialog_type="success", parent=self).exec()
        except Exception as e:
            from geoview_pyside6.widgets.confirm_dialog import ConfirmDialog

            ConfirmDialog(t("common.error"), str(e), confirm_text="OK", cancel_text="", dialog_type="warning", parent=self).exec()
    def retranslate(self):
        """Update all translatable strings to the current language."""
        self._title.setText(t("settings.title"))
        self._guide_label.setText(t("guide.settings"))

        # Language group
        self._lang_group.setTitle(t("settings.language"))
        self._lang_combo.blockSignals(True)
        current_data = self._lang_combo.currentData()
        self._lang_combo.clear()
        self._lang_combo.addItem(t("settings.lang_ko"), "ko")
        self._lang_combo.addItem(t("settings.lang_en"), "en")
        idx = self._lang_combo.findData(current_data)
        if idx >= 0:
            self._lang_combo.setCurrentIndex(idx)
        self._lang_combo.blockSignals(False)

        # Monitoring
        self._monitor_group.setTitle(t("settings.monitoring"))
        self._ping_interval_label.setText(t("settings.ping_interval"))
        self._interface_poll_label.setText(t("settings.interface_poll"))
        self._delay_threshold_label.setText(t("settings.delay_threshold"))

        # Alerts
        self._alert_group.setTitle(t("settings.alerts"))
        self._alert_enabled.setText(t("settings.alert_enabled"))
        self._sound_enabled.setText(t("settings.sound_enabled"))
        self._escalation_enabled.setText(t("settings.escalation"))

        # Vessel Presets
        self._preset_group.setTitle(t("settings.vessel_presets"))
        self._preset_desc.setText(t("settings.preset_desc"))
        self._load_preset_btn.setText(t("settings.load_preset"))
        self._import_yaml_btn.setText(t("settings.import_yaml"))

        # Profiles
        self._profile_group.setTitle(t("settings.profiles"))
        self._profile_desc.setText(t("settings.profile_desc"))
        self._profile_name_input.setPlaceholderText(t("settings.profile_name"))
        self._vessel_input.setPlaceholderText(t("settings.vessel_name"))
        self._save_profile_btn.setText(t("settings.save_current"))
        self._load_profile_btn.setText(t("settings.load"))
        self._del_profile_btn.setText(t("settings.delete"))

        # Backups
        self._backup_group.setTitle(t("settings.safety_backups"))
        self._backup_desc.setText(t("settings.backup_desc"))
        self._refresh_backup_btn.setText(t("settings.refresh"))
        self._create_backup_btn.setText(t("settings.create_backup"))
        self._restore_backup_btn.setText(t("settings.restore"))

        # Config
        self._config_group.setTitle(t("settings.configuration"))
        self._import_btn.setText(t("settings.import_config"))
        self._export_btn.setText(t("settings.export_config"))

        # Save button
        self._save_btn.setText(t("settings.save_settings"))

        # Refresh backup combo placeholder
        self._refresh_backups()
