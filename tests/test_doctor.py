"""Tests for the local-only PortDetector preflight / doctor surface."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from backend.services import doctor_service


def _runtime_context(tmp_path: Path, mode: str = "source") -> dict[str, object]:
    bundle_dir = tmp_path / "bundle"
    (bundle_dir / "frontend" / "templates").mkdir(parents=True, exist_ok=True)
    (bundle_dir / "frontend" / "static").mkdir(parents=True, exist_ok=True)
    (bundle_dir / "assets").mkdir(parents=True, exist_ok=True)
    (bundle_dir / "assets" / "icon.ico").write_text("icon", encoding="utf-8")

    return {
        "mode": mode,
        "is_frozen": mode == "packaged",
        "base_dir": str(tmp_path),
        "bundle_dir": str(bundle_dir),
        "entrypoint": str(tmp_path / "entrypoint.py"),
    }


def test_run_preflight_reports_pass_warning_and_local_only_boundary(tmp_path):
    class _TrafficService:
        def start(self):
            return None

        def is_available(self):
            return False

        def stop(self):
            return None

    def fake_import_module(name):
        return SimpleNamespace(__name__=name)

    report = doctor_service.run_preflight(
        str(tmp_path / "data"),
        "web",
        runtime_context=_runtime_context(tmp_path),
        import_module=fake_import_module,
        traffic_service_factory=_TrafficService,
    )

    text = report.render()

    assert report.exit_code == 0
    assert "[PASS] bundle parity" in text
    assert "[PASS] config" in text
    assert "[PASS] storage" in text
    assert "[WARN] monitoring" in text
    assert "local-only" in text.lower()
    assert "does not verify live devices" in text.lower()
    assert "resources:" in text.lower()
    assert [resource["relative_path"] for resource in report.runtime["resources"]] == [
        "frontend/templates",
        "frontend/static",
        "assets/icon.ico",
    ]


def test_run_preflight_fails_closed_on_invalid_existing_config(tmp_path):
    class _TrafficService:
        def start(self):
            return None

        def is_available(self):
            return True

        def stop(self):
            return None

    def fake_import_module(name):
        return SimpleNamespace(__name__=name)

    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    config_path = data_dir / "devices.json"
    original_text = '{"version": 1, "settings": {"web_port": "oops"}, "devices": []}'
    config_path.write_text(original_text, encoding="utf-8")

    report = doctor_service.run_preflight(
        str(data_dir),
        "desktop",
        runtime_context=_runtime_context(tmp_path, mode="packaged"),
        import_module=fake_import_module,
        traffic_service_factory=_TrafficService,
    )

    text = report.render()

    assert report.exit_code == 1
    assert "[FAIL] config" in text
    assert "invalid" in text.lower()
    assert config_path.read_text(encoding="utf-8") == original_text


def test_export_operator_packet_writes_json_packet(tmp_path):
    class _TrafficService:
        def start(self):
            return None

        def is_available(self):
            return True

        def stop(self):
            return None

    def fake_import_module(name):
        return SimpleNamespace(__name__=name)

    report = doctor_service.run_preflight(
        str(tmp_path / "data"),
        "desktop",
        runtime_context=_runtime_context(tmp_path, mode="packaged"),
        import_module=fake_import_module,
        traffic_service_factory=_TrafficService,
    )

    saved = doctor_service.export_operator_packet(
        report,
        str(tmp_path / "doctor_packet"),
    )

    payload = json.loads((tmp_path / "doctor_packet.json").read_text(encoding="utf-8"))

    assert saved.endswith(".json")
    assert payload["title"] == "PortDetector operator packet"
    assert payload["boundary"].startswith("Boundary: local-only")
    assert payload["summary"]["result"] == "PASS"
    assert payload["runtime"]["mode"] == "packaged"
    assert any(check["name"] == "bundle parity" for check in payload["checks"])
    assert payload["checks"]
    assert [resource["relative_path"] for resource in payload["runtime"]["resources"]] == [
        "assets/icon.ico",
    ]
    assert payload["runtime"]["resources"][0]["required"] is True


def test_export_operator_packet_leaves_existing_file_intact_on_write_failure(tmp_path, monkeypatch):
    class _TrafficService:
        def start(self):
            return None

        def is_available(self):
            return True

        def stop(self):
            return None

    def fake_import_module(name):
        return SimpleNamespace(__name__=name)

    report = doctor_service.run_preflight(
        str(tmp_path / "data"),
        "desktop",
        runtime_context=_runtime_context(tmp_path, mode="packaged"),
        import_module=fake_import_module,
        traffic_service_factory=_TrafficService,
    )

    packet_path = tmp_path / "doctor_packet.json"
    packet_path.write_text("previous packet", encoding="utf-8")
    def fake_replace(src, dst):
        raise RuntimeError("simulated export failure")

    monkeypatch.setattr(doctor_service.os, "replace", fake_replace)

    with pytest.raises(RuntimeError):
        doctor_service.export_operator_packet(report, str(tmp_path / "doctor_packet"))

    assert packet_path.read_text(encoding="utf-8") == "previous packet"


def test_desktop_preflight_does_not_require_geoview_runtime_import(tmp_path):
    class _TrafficService:
        def start(self):
            return None

        def is_available(self):
            return True

        def stop(self):
            return None

    def fake_import_module(name):
        if name == "geoview_pyside6.runtime":
            raise AssertionError("desktop doctor should not import the full GeoView GUI stack")
        return SimpleNamespace(__name__=name)

    report = doctor_service.run_preflight(
        str(tmp_path / "data"),
        "desktop",
        runtime_context=_runtime_context(tmp_path, mode="packaged"),
        import_module=fake_import_module,
        traffic_service_factory=_TrafficService,
    )

    assert report.exit_code == 0
    assert any(check.name == "bundle parity" and check.status == "PASS" for check in report.checks)


def test_desktop_runtime_context_uses_executable_root_when_frozen(monkeypatch):
    import main

    monkeypatch.setattr(main.sys, "frozen", True, raising=False)
    monkeypatch.setattr(main.sys, "executable", r"C:\\Apps\\PortDetector\\PortDetector.exe", raising=False)
    monkeypatch.setattr(main.sys, "_MEIPASS", r"C:\\Temp\\_MEI123", raising=False)
    monkeypatch.setattr(main, "__file__", r"C:\\Temp\\_MEI123\\main.py", raising=False)

    context = main.build_runtime_context()

    assert context["mode"] == "packaged"
    assert context["is_frozen"] is True
    assert context["base_dir"] == r"C:\\Apps\\PortDetector"
    assert context["bundle_dir"] == r"C:\\Temp\\_MEI123"
    assert context["entrypoint"] == r"C:\\Apps\\PortDetector\\PortDetector.exe"


def test_run_preflight_fails_when_web_dependency_is_missing(tmp_path):
    class _TrafficService:
        def start(self):
            return None

        def is_available(self):
            return True

        def stop(self):
            return None

    def fake_import_module(name):
        if name == "flask_socketio":
            raise ImportError("No module named flask_socketio")
        return SimpleNamespace(__name__=name)

    report = doctor_service.run_preflight(
        str(tmp_path),
        "web",
        import_module=fake_import_module,
        traffic_service_factory=_TrafficService,
    )

    text = report.render()

    assert report.exit_code == 1
    assert "[FAIL] dependencies" in text
    assert "flask_socketio" in text


def test_app_and_main_doctor_flag_dispatches_without_starting_ui_or_server(monkeypatch):
    import app
    import main

    app_calls = []
    main_calls = []

    monkeypatch.setattr(app, "run_doctor", lambda export_path=None: app_calls.append(("doctor", export_path)) or 0)
    monkeypatch.setattr(app, "run_web_app", lambda: app_calls.append("web") or 0)
    monkeypatch.setattr(main, "run_doctor", lambda export_path=None: main_calls.append(("doctor", export_path)) or 0)
    monkeypatch.setattr(main, "run_desktop_app", lambda: main_calls.append("desktop") or 0)

    assert app.main(["--doctor"]) == 0
    assert main.main(["--doctor"]) == 0
    assert app_calls == [("doctor", None)]
    assert main_calls == [("doctor", None)]


def test_doctor_export_flag_is_forwarded_to_entrypoints(monkeypatch):
    import app
    import main

    app_exports = []
    main_exports = []

    monkeypatch.setattr(app, "run_doctor", lambda export_path=None: app_exports.append(export_path) or 0)
    monkeypatch.setattr(main, "run_doctor", lambda export_path=None: main_exports.append(export_path) or 0)

    assert app.main(["--doctor", "--doctor-export", "out/web-doctor"]) == 0
    assert main.main(["--doctor", "--doctor-export", "out/desktop-doctor"]) == 0
    assert app_exports == ["out/web-doctor"]
    assert main_exports == ["out/desktop-doctor"]


def test_portdetector_spec_keeps_numpy_available_for_packaged_runtime():
    spec_text = (Path(__file__).resolve().parents[1] / "PortDetector.spec").read_text(encoding="utf-8")

    assert "'numpy'" in spec_text
    assert "'numpy'," not in spec_text.split("excludes=[", 1)[1]


def test_build_bat_fails_closed_when_packaged_exe_is_still_running():
    build_text = (Path(__file__).resolve().parents[1] / "build.bat").read_text(encoding="utf-8")

    assert "RUNNING_PORTDETECTOR_PID" in build_text
    assert "Existing packaged PortDetector.exe is still running" in build_text


def test_build_bat_uses_isolated_pyinstaller_workpath():
    build_text = (Path(__file__).resolve().parents[1] / "build.bat").read_text(encoding="utf-8")

    assert "PYI_WORKDIR" in build_text
    assert "--workpath" in build_text
