## 2026-04-05 02:49 — PortDetector reliability
Scope:    backend/services/config_service.py, tests/test_security.py — reliability proof + snapshot safety
Summary:  Hardened config export to return an isolated snapshot and added a config/profile round-trip test.
Files:    backend/services/config_service.py, tests/test_security.py
Verification: python -m py_compile backend\services\config_service.py tests\test_security.py; pytest tests\test_security.py -q; pytest tests\test_desktop_smoke.py -q
Next:     If needed, extend the same pattern to backup restore/load round-trips.

## 2026-04-14 14:38 — PortDetector preflight doctor
Scope:    app.py, main.py, backend/services/doctor_service.py, run.bat, README.md, tests/test_doctor.py — local-only preflight surface
Summary:  Added `--doctor` to both startup entrypoints and batch forwarding so operators can verify config, storage, backup, dependency, and monitoring prerequisites before live use.
Files:    app.py, main.py, backend/services/doctor_service.py, run.bat, README.md, tests/test_doctor.py, SESSION_STATUS.md
Verification: python -m py_compile app.py main.py backend\services\doctor_service.py tests\test_doctor.py; pytest tests/test_doctor.py -q; pytest tests/test_security.py -q; pytest tests/test_export_service.py -q; pytest tests/test_desktop_smoke.py -q; python app.py --doctor; python main.py --doctor; cmd /c run.bat --doctor
Next:     If we want a future tranche, we can add a machine-readable JSON output mode for automation.

## 2026-04-14 14:55 — PortDetector operator packet export
Scope:    app.py, main.py, backend/services/doctor_service.py, README.md, tests/test_doctor.py, WORKLOG.md, SESSION_STATUS.md — reusable doctor export seam
Summary:  Added a JSON operator packet export path to the doctor report so fresh-machine checks can reuse the same local-only preflight data without implying live device reachability.
Files:    app.py, main.py, backend/services/doctor_service.py, README.md, tests/test_doctor.py, WORKLOG.md, SESSION_STATUS.md
Verification: pending focused py_compile/pytest run
Next:     Confirm the new export path, then keep the wording local-only in any future operator-facing docs.

## 2026-04-14 16:35 — PortDetector bundle parity proof
Scope:    app.py, main.py, backend/services/doctor_service.py, tests/test_doctor.py, README.md, SESSION_STATUS.md, WORKLOG.md — bounded bundle/runtime proof artifact
Summary:  Added a local-only bundle parity check to the doctor packet so the operator export now records runtime source-vs-packaged paths, required resource presence, and optional asset status without making live-device claims.
Files:    app.py, main.py, backend/services/doctor_service.py, tests/test_doctor.py, README.md, SESSION_STATUS.md, WORKLOG.md
Verification: python -m py_compile app.py main.py backend\services\doctor_service.py tests\test_doctor.py; pytest tests/test_doctor.py -q; python app.py --doctor; python main.py --doctor
Next:     If we harden packaging further, the next safe seam is a build step that emits the same operator packet alongside the packaged artifact.

## 2026-04-15 08:31 — PortDetector layout fail-closed hardening
Scope:    backend/services/network_map_service.py, tests/test_security.py, SESSION_STATUS.md, WORKLOG.md — atomic layout save + malformed-layout fail-closed
Summary:  Made layout saves atomic, made malformed layout JSON return an empty load result, and stopped malformed layouts from surfacing as zero-node valid entries in the layout list.
Files:    backend/services/network_map_service.py, tests/test_security.py, SESSION_STATUS.md, WORKLOG.md
Verification: python -m py_compile backend\services\network_map_service.py tests\test_security.py; pytest tests\test_security.py tests\test_doctor.py -q; cmd /c build.bat
Next:     If we see another packaged-build seam, the next likely target is a deeper operator packet consistency check between source and frozen runtime payloads.
