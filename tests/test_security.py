"""Security and safety regression tests for PortDetector."""

from __future__ import annotations

import builtins
import json
import os
import threading
import time
from pathlib import Path

import pytest

import backend.services.backup_service as backup_module
import backend.services.config_service as config_module
import backend.services.log_service as log_module
from backend.services.backup_service import BackupService
from backend.services.config_service import ConfigService
from backend.services.profile_service import ProfileService
from backend.models.device import Device
from backend.services.log_service import LogService
from config import load_or_create_secret_key


def test_load_or_create_secret_key_persists(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("PORTDETECTOR_SECRET_KEY", raising=False)

    first = load_or_create_secret_key(str(tmp_path))
    second = load_or_create_secret_key(str(tmp_path))

    assert first
    assert first == second
    assert (tmp_path / "portdetector.secret").read_text(encoding="utf-8").strip() == first


def test_load_or_create_secret_key_prefers_env(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("PORTDETECTOR_SECRET_KEY", "env-secret-value")

    loaded = load_or_create_secret_key(str(tmp_path))

    assert loaded == "env-secret-value"
    assert not (tmp_path / "portdetector.secret").exists()


def test_load_backup_rejects_path_traversal(tmp_path: Path):
    service = BackupService(str(tmp_path))
    backups_dir = tmp_path / "backups"
    backups_dir.mkdir(parents=True, exist_ok=True)
    good_file = backups_dir / "safe.json"
    good_file.write_text('{"config": {"devices": []}}', encoding="utf-8")

    assert service.load_backup("safe.json") is not None
    assert service.load_backup("../safe.json") is None
    assert service.load_backup(r"..\\safe.json") is None


def test_backup_restore_round_trip_proves_config_and_devices(tmp_path: Path):
    config_service = ConfigService(str(tmp_path))
    backup_service = BackupService(str(tmp_path))

    device = Device(
        name="Bridge Monitor",
        ip="10.0.0.25",
        ports=[22, 443],
        category="Network",
        importance="high",
        description="Round-trip fixture",
        enabled=False,
    )
    created = config_service.add_device(device)
    snapshot = config_service.export_config()
    restored_device = snapshot["devices"][-1]
    backup = backup_service.create_backup(snapshot, "manual-backup", "round-trip proof")

    config_service.update_settings(
        {
            "web_port": 7001,
            "alert_enabled": True,
            "sound_enabled": True,
        }
    )
    config_service.update_device(created.id, {"name": "Mutated Bridge Monitor"})

    restored = backup_service.restore_backup(backup["filename"])
    assert restored is not None
    assert restored["device_count"] == len(snapshot["devices"])
    assert restored["config"] == snapshot

    config_service.import_config(restored["config"])
    reloaded = ConfigService(str(tmp_path))

    assert reloaded.export_config() == snapshot
    assert reloaded.get_settings()["web_port"] == snapshot["settings"]["web_port"]
    assert reloaded.get_settings()["alert_enabled"] == snapshot["settings"]["alert_enabled"]
    assert any(
        dev.id == restored_device["id"] and dev.name == restored_device["name"]
        for dev in reloaded.get_devices()
    )


def test_log_event_redacts_sensitive_extra_fields(tmp_path: Path):
    service = LogService(str(tmp_path))

    service.log_event(
        "dev_001",
        "10.0.0.1",
        "connected",
        rtt_ms=12,
        token="abc123",
        note="visible",
        nested={"api_key": "secret-1", "keep": "ok"},
    )

    entry = service.get_history(limit=1)[0]

    assert entry["token"] == "[REDACTED]"
    assert entry["nested"]["api_key"] == "[REDACTED]"
    assert entry["nested"]["keep"] == "ok"
    assert entry["note"] == "visible"


def test_log_event_serializes_rotation_and_append(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(log_module, "MAX_LOG_SIZE_BYTES", 1024)
    monkeypatch.setattr(log_module, "MAX_LOG_BACKUPS", 1)

    log_path = tmp_path / "history.log"
    log_path.write_text("x" * 2048, encoding="utf-8")

    service_a = LogService(str(tmp_path))
    service_b = LogService(str(tmp_path))

    original_remove = log_module.os.remove
    entered_first_remove = threading.Event()
    allow_first_remove_to_finish = threading.Event()
    active_removals = 0
    max_active_removals = 0
    state_lock = threading.Lock()
    errors = []

    def fake_remove(path):
        nonlocal active_removals, max_active_removals
        with state_lock:
            active_removals += 1
            max_active_removals = max(max_active_removals, active_removals)
            if active_removals == 1:
                entered_first_remove.set()
        try:
            if not allow_first_remove_to_finish.wait(timeout=2):
                raise AssertionError("rotation gate timed out")
            return original_remove(path)
        finally:
            with state_lock:
                active_removals -= 1

    monkeypatch.setattr(log_module.os, "remove", fake_remove)

    def write_event(service, device_id):
        try:
            service.log_event(device_id, "10.0.0.1", "connected")
        except Exception as exc:  # pragma: no cover - surfaced by assertions
            errors.append(exc)

    thread_a = threading.Thread(target=write_event, args=(service_a, "dev_a"))
    thread_b = threading.Thread(target=write_event, args=(service_b, "dev_b"))

    thread_a.start()
    assert entered_first_remove.wait(timeout=2)
    thread_b.start()
    time.sleep(0.25)
    allow_first_remove_to_finish.set()

    thread_a.join(timeout=2)
    thread_b.join(timeout=2)

    assert not thread_a.is_alive()
    assert not thread_b.is_alive()
    assert not errors
    assert max_active_removals == 1

    entries = service_a.get_history(limit=10)
    assert {entry["device_id"] for entry in entries} == {"dev_a", "dev_b"}


def test_get_history_waits_for_rotation_snapshot(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(log_module, "MAX_LOG_SIZE_BYTES", 1024)
    monkeypatch.setattr(log_module, "MAX_LOG_BACKUPS", 1)

    log_path = tmp_path / "history.log"
    log_path.write_text("x" * 2048, encoding="utf-8")

    service = LogService(str(tmp_path))

    original_remove = log_module.os.remove
    original_open = builtins.open
    entered_remove = threading.Event()
    allow_remove_to_finish = threading.Event()
    reader_opened = threading.Event()
    errors = []
    results = []

    def fake_remove(path):
        entered_remove.set()
        if not allow_remove_to_finish.wait(timeout=2):
            raise AssertionError("rotation gate timed out")
        return original_remove(path)

    def tracked_open(file, mode="r", *args, **kwargs):
        if Path(file) == log_path and "r" in mode and "b" in mode:
            reader_opened.set()
        return original_open(file, mode, *args, **kwargs)

    monkeypatch.setattr(log_module.os, "remove", fake_remove)
    monkeypatch.setattr(builtins, "open", tracked_open)

    def write_event():
        try:
            service.log_event("dev_a", "10.0.0.1", "connected")
        except Exception as exc:  # pragma: no cover - surfaced by assertions
            errors.append(exc)

    def read_history():
        try:
            results.append(service.get_history(limit=10))
        except Exception as exc:  # pragma: no cover - surfaced by assertions
            errors.append(exc)

    writer = threading.Thread(target=write_event)
    reader = threading.Thread(target=read_history)

    writer.start()
    assert entered_remove.wait(timeout=2)
    reader.start()

    time.sleep(0.2)
    assert not reader_opened.is_set()

    allow_remove_to_finish.set()
    writer.join(timeout=2)
    reader.join(timeout=2)

    assert not writer.is_alive()
    assert not reader.is_alive()
    assert not errors
    assert len(results) == 1
    assert {entry["device_id"] for entry in results[0]} == {"dev_a"}


def test_create_backup_prunes_old_files(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(backup_module, "MAX_CONFIG_BACKUPS", 2)
    service = backup_module.BackupService(str(tmp_path))

    backups_dir = tmp_path / "backups"
    backups_dir.mkdir(parents=True, exist_ok=True)

    for index in range(3):
        path = backups_dir / f"2026040{index + 1}_000000_old_{index}.json"
        path.write_text('{"config": {"devices": []}}', encoding="utf-8")
        os.utime(path, (100 + index, 100 + index))

    created = service.create_backup({"devices": []}, "dashboard", "note")
    files = sorted(path.name for path in backups_dir.glob("*.json"))

    assert created["filename"] in files
    assert len(files) == 2
    assert "20260401_000000_old_0.json" not in files
    assert "20260402_000000_old_1.json" not in files


def test_config_save_is_atomic_on_failure(tmp_path: Path, monkeypatch):
    config_path = tmp_path / "devices.json"
    original_config = {
        "version": 1,
        "settings": {
            "web_port": 5555,
        },
        "devices": [],
    }
    config_path.write_text(json.dumps(original_config, indent=2), encoding="utf-8")
    service = ConfigService(str(tmp_path))
    original_text = config_path.read_text(encoding="utf-8")

    def failing_dump(obj, fp, *args, **kwargs):
        fp.write('{"partial": true')
        fp.flush()
        raise RuntimeError("simulated write failure")

    monkeypatch.setattr(config_module.json, "dump", failing_dump)

    with pytest.raises(RuntimeError):
        service.update_settings({"web_port": 6000})

    assert config_path.read_text(encoding="utf-8") == original_text

    reloaded = ConfigService(str(tmp_path))
    assert reloaded.get_settings()["web_port"] == 5555


def test_config_profile_round_trip_uses_snapshot_copy(tmp_path: Path):
    config_service = ConfigService(str(tmp_path))
    profile_service = ProfileService(str(tmp_path))

    device = Device(
        name="Bridge Monitor",
        ip="10.0.0.25",
        ports=[22, 443],
        category="Network",
        importance="high",
        description="Round-trip fixture",
        enabled=False,
    )
    created = config_service.add_device(device)
    settings = config_service.update_settings(
        {
            "web_port": 6010,
            "alert_enabled": False,
            "sound_enabled": False,
        }
    )

    exported = config_service.export_config()
    exported["settings"]["web_port"] = 9999

    assert config_service.get_settings()["web_port"] == 6010

    profile_filename = profile_service.save_profile(
        "round trip",
        exported["devices"],
        settings,
        vessel="Test Vessel",
        description="Config/profile round-trip proof",
    )

    config_service.update_settings({"web_port": 7000, "alert_enabled": True})
    config_service.delete_device(created.id)

    loaded_profile = profile_service.load_profile(profile_filename)
    assert loaded_profile is not None
    assert loaded_profile["settings"]["web_port"] == 6010
    assert loaded_profile["vessel"] == "Test Vessel"
    assert loaded_profile["description"] == "Config/profile round-trip proof"

    config_service.import_config(loaded_profile)

    restored_devices = config_service.get_devices()
    assert config_service.get_settings()["web_port"] == 6010
    assert config_service.get_settings()["alert_enabled"] is False
    assert config_service.get_settings()["sound_enabled"] is False
    assert len(restored_devices) == 2
    assert any(dev.id == created.id and dev.name == created.name for dev in restored_devices)
