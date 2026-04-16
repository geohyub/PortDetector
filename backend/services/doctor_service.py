"""Local-only preflight checks for PortDetector startup surfaces."""

from __future__ import annotations

import json
import importlib
import os
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Callable, Mapping

from config import load_or_create_secret_key
from backend.services.backup_service import BackupService
from backend.services.config_service import ConfigService
from backend.services.import_validation import validate_config_payload
from backend.services.log_service import LogService


PASS = "PASS"
WARN = "WARN"
FAIL = "FAIL"
DOCTOR_SCOPE = "config, storage, backups, and monitoring prerequisites"
DOCTOR_BOUNDARY = (
    "Boundary: local-only; this does not verify live devices, remote ports, "
    "browser launch, or long-running packet capture."
)
DOCTOR_RESOURCE_RELATIVE_PATHS = {
    "web": (
        ("frontend/templates", "frontend templates", True),
        ("frontend/static", "frontend static", True),
        ("assets/icon.ico", "application icon", False),
    ),
    "desktop": (
        ("assets/icon.ico", "application icon", True),
    ),
}


@dataclass
class DoctorCheck:
    name: str
    status: str
    message: str


@dataclass
class DoctorReport:
    surface: str
    data_dir: str
    runtime: dict[str, object] = field(default_factory=dict)
    checks: list[DoctorCheck] = field(default_factory=list)

    def add(self, name: str, status: str, message: str) -> None:
        self.checks.append(DoctorCheck(name=name, status=status, message=message))

    @property
    def exit_code(self) -> int:
        return 1 if any(check.status == FAIL for check in self.checks) else 0

    def counts(self) -> dict[str, int]:
        counts = {PASS: 0, WARN: 0, FAIL: 0}
        for check in self.checks:
            counts[check.status] = counts.get(check.status, 0) + 1
        return counts

    def operator_packet(self) -> dict[str, object]:
        counts = self.counts()
        return {
            "title": "PortDetector operator packet",
            "surface": self.surface,
            "data_dir": self.data_dir,
            "runtime": dict(self.runtime),
            "scope": DOCTOR_SCOPE,
            "boundary": DOCTOR_BOUNDARY,
            "summary": {
                "pass": counts.get(PASS, 0),
                "warn": counts.get(WARN, 0),
                "fail": counts.get(FAIL, 0),
                "result": "PASS" if self.exit_code == 0 else "FAIL",
                "exit_code": self.exit_code,
            },
            "checks": [
                {
                    "name": check.name,
                    "status": check.status,
                    "message": check.message,
                }
                for check in self.checks
            ],
        }

    def render(self) -> str:
        packet = self.operator_packet()
        summary = packet["summary"]
        lines = [
            packet["title"],
            f"Surface: {packet['surface']}",
            f"Data dir: {packet['data_dir']}",
            f"Runtime: {packet['runtime'].get('mode', 'source')}",
            f"Base dir: {packet['runtime'].get('base_dir', 'n/a')}",
            f"Bundle dir: {packet['runtime'].get('bundle_dir', 'n/a')}",
            f"Scope: {packet['scope']}",
            packet["boundary"],
            "",
        ]
        resource_checks = packet["runtime"].get("resources", [])
        if resource_checks:
            resource_summary = ", ".join(
                f"{resource['label']}="
                f"{'yes' if resource['exists'] else ('no' if resource.get('required') else 'optional-missing')}"
                for resource in resource_checks
            )
            lines.append(f"Resources: {resource_summary}")
            lines.append("")
        for check in packet["checks"]:
            lines.append(f"[{check['status']}] {check['name']}: {check['message']}")
        lines.extend([
            "",
            f"SUMMARY: pass={summary['pass']} warn={summary['warn']} fail={summary['fail']}",
            f"RESULT: {summary['result']}",
        ])
        return "\n".join(lines)


def _probe_writable_path(directory: str, label: str) -> tuple[bool, str]:
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    try:
        with NamedTemporaryFile(
            "w",
            delete=False,
            dir=str(path),
            prefix=".doctor-",
            suffix=".probe",
            encoding="utf-8",
        ) as tmp:
            tmp.write("probe")
            tmp.flush()
            os.fsync(tmp.fileno())
            probe_path = Path(tmp.name)
        probe_path.unlink(missing_ok=True)
        return True, f"{label} writable"
    except OSError as exc:
        return False, f"{label} is not writable: {exc}"


def _check_dependencies(surface: str, import_module: Callable[[str], object]) -> tuple[str, str]:
    surface_modules = {
        "web": ["flask", "flask_socketio"],
        # Keep the desktop doctor bounded to the frozen entrypoint's immediate
        # Qt runtime surface; the full GeoView shared GUI stack is a separate
        # launch path and is too heavy for this packaged-proof seam.
        "desktop": ["PySide6.QtWidgets", "PySide6.QtCore", "PySide6.QtNetwork"],
    }
    modules = surface_modules.get(surface)
    if modules is None:
        return FAIL, f"unknown surface '{surface}'"

    missing = []
    for module_name in modules:
        try:
            import_module(module_name)
        except Exception as exc:  # pragma: no cover - exercised through tests
            missing.append(f"{module_name} ({exc})")

    if missing:
        return FAIL, "missing runtime dependencies: " + "; ".join(missing)
    return PASS, "surface runtime dependencies available"


def _check_config(data_dir: str) -> tuple[str, str]:
    config_path = Path(data_dir) / "devices.json"
    config_exists = config_path.exists()

    if config_exists:
        try:
            with config_path.open("r", encoding="utf-8") as f:
                validate_config_payload(json.load(f))
        except (json.JSONDecodeError, OSError, ValueError) as exc:
            return FAIL, f"existing devices.json is invalid and would be reset on startup: {exc}"

    try:
        config_service = ConfigService(data_dir)
        settings = config_service.get_settings()
        devices = config_service.get_devices()
        if not isinstance(settings, dict):
            return FAIL, "settings did not load as a mapping"
        if config_exists:
            return PASS, f"loaded devices.json with {len(settings)} settings and {len(devices)} device(s)"
        return PASS, f"created default devices.json with {len(settings)} settings and {len(devices)} device(s)"
    except Exception as exc:
        return FAIL, f"config load failed: {exc}"


def _check_storage(data_dir: str) -> list[DoctorCheck]:
    checks: list[DoctorCheck] = []

    ok, message = _probe_writable_path(data_dir, "data directory")
    checks.append(DoctorCheck("storage", PASS if ok else FAIL, message))

    ok, message = _probe_writable_path(os.path.join(data_dir, "backups"), "backups directory")
    checks.append(DoctorCheck("backups storage", PASS if ok else FAIL, message))

    return checks


def _check_history(data_dir: str) -> tuple[str, str]:
    try:
        log_service = LogService(data_dir)
        entries = log_service.get_history(limit=1)
        return PASS, f"history log readable ({len(entries)} recent entr{'y' if len(entries) == 1 else 'ies'})"
    except Exception as exc:
        return FAIL, f"history log check failed: {exc}"


def _build_runtime_snapshot(
    data_dir: str,
    surface: str,
    runtime_context: Mapping[str, object] | None = None,
) -> dict[str, object]:
    runtime_context = dict(runtime_context or {})
    base_dir = Path(str(runtime_context.get("base_dir") or Path(data_dir).resolve().parent))
    bundle_dir = Path(str(runtime_context.get("bundle_dir") or base_dir))
    mode = str(runtime_context.get("mode") or ("packaged" if base_dir != bundle_dir else "source"))
    is_frozen = bool(runtime_context.get("is_frozen", mode == "packaged"))
    entrypoint = str(runtime_context.get("entrypoint") or "")

    resources = []
    for relative_path, label, required in DOCTOR_RESOURCE_RELATIVE_PATHS.get(surface, ()):
        resource_path = bundle_dir / relative_path
        resources.append(
            {
                "label": label,
                "relative_path": relative_path,
                "path": str(resource_path),
                "exists": resource_path.exists(),
                "required": required,
            }
        )

    return {
        "mode": mode,
        "is_frozen": is_frozen,
        "base_dir": str(base_dir),
        "bundle_dir": str(bundle_dir),
        "entrypoint": entrypoint,
        "resources": resources,
    }


def _check_bundle_parity(runtime: Mapping[str, object]) -> tuple[str, str]:
    resources = runtime.get("resources", [])
    required_missing = [
        resource["label"]
        for resource in resources
        if resource.get("required") and not resource.get("exists")
    ]
    optional_missing = [
        resource["label"]
        for resource in resources
        if not resource.get("required") and not resource.get("exists")
    ]

    if required_missing:
        return FAIL, "bundle/runtime proof missing required resources: " + ", ".join(required_missing)

    mode = runtime.get("mode", "source")
    base_dir = runtime.get("base_dir", "n/a")
    bundle_dir = runtime.get("bundle_dir", "n/a")
    optional_note = ""
    if optional_missing:
        optional_note = "; optional resources missing: " + ", ".join(optional_missing)
    if mode == "packaged":
        message = f"packaged runtime resolved via base_dir={base_dir} and bundle_dir={bundle_dir}; required resources are present{optional_note}"
    else:
        message = f"source runtime resolved via base_dir={base_dir}; required resources are present{optional_note}"
    if optional_missing:
        return WARN, message
    return PASS, message


def _check_backups(data_dir: str) -> tuple[str, str]:
    try:
        backup_service = BackupService(data_dir)
        backups = backup_service.list_backups()
        if not backups:
            return WARN, "no backups found yet; directory is reachable, but restore data has not been created"

        latest = backups[0]
        loaded = backup_service.restore_backup(latest["filename"])
        if not loaded:
            return FAIL, f"latest backup could not be loaded: {latest['filename']}"
        return PASS, f"loaded latest backup {latest['filename']} ({loaded.get('device_count', 0)} device(s))"
    except Exception as exc:
        return FAIL, f"backup check failed: {exc}"


def _check_web_secret(data_dir: str) -> tuple[str, str]:
    try:
        key = load_or_create_secret_key(data_dir)
        if not key:
            return FAIL, "secret key could not be created"
        return PASS, "local secret key is available"
    except Exception as exc:
        return FAIL, f"secret key check failed: {exc}"


def _check_monitoring(traffic_service_factory) -> tuple[str, str]:
    try:
        import_module = importlib.import_module
        import_module("psutil")
    except Exception as exc:
        return FAIL, f"monitoring dependency missing: psutil ({exc})"

    try:
        service = traffic_service_factory()
        service.start()
        available = service.is_available()
        service.stop()
        if available:
            return PASS, "traffic capture can start on this machine"
        return WARN, "traffic capture is not available here; run as administrator to enable packet capture"
    except Exception as exc:
        return FAIL, f"traffic capture probe failed: {exc}"


def run_preflight(
    data_dir: str,
    surface: str,
    *,
    runtime_context: Mapping[str, object] | None = None,
    import_module: Callable[[str], object] = importlib.import_module,
    traffic_service_factory=None,
) -> DoctorReport:
    """Run a bounded local-only preflight for the requested startup surface."""

    if traffic_service_factory is None:
        from backend.services.traffic_service import TrafficService
        traffic_service_factory = TrafficService

    runtime = _build_runtime_snapshot(data_dir, surface, runtime_context)
    report = DoctorReport(surface=surface, data_dir=data_dir, runtime=runtime)

    status, message = _check_dependencies(surface, import_module)
    report.add("dependencies", status, message)

    status, message = _check_bundle_parity(runtime)
    report.add("bundle parity", status, message)

    status, message = _check_config(data_dir)
    report.add("config", status, message)

    for check in _check_storage(data_dir):
        report.checks.append(check)

    status, message = _check_history(data_dir)
    report.add("history", status, message)

    status, message = _check_backups(data_dir)
    report.add("backups", status, message)

    if surface == "web":
        status, message = _check_web_secret(data_dir)
        report.add("web secret", status, message)

    status, message = _check_monitoring(traffic_service_factory)
    report.add("monitoring", status, message)

    return report


def print_preflight(report: DoctorReport, *, printer=print) -> int:
    printer(report.render())
    return report.exit_code


def export_operator_packet(report: DoctorReport, output_path: str) -> str:
    """Write the doctor report as a reusable JSON operator packet."""

    path = Path(output_path)
    if path.suffix.lower() != ".json":
        path = path.with_suffix(".json")
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        with NamedTemporaryFile(
            "w",
            delete=False,
            dir=str(path.parent),
            prefix=f".{path.stem}-",
            suffix=".tmp",
            encoding="utf-8",
        ) as tmp:
            temp_path = Path(tmp.name)
            tmp.write(json.dumps(report.operator_packet(), ensure_ascii=False, indent=2) + "\n")
            tmp.flush()
            os.fsync(tmp.fileno())
        os.replace(temp_path, path)
    except Exception:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
        raise
    return str(path)
