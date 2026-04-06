## 2026-04-05 02:49 — PortDetector reliability
Scope:    backend/services/config_service.py, tests/test_security.py — reliability proof + snapshot safety
Summary:  Hardened config export to return an isolated snapshot and added a config/profile round-trip test.
Files:    backend/services/config_service.py, tests/test_security.py
Verification: python -m py_compile backend\services\config_service.py tests\test_security.py; pytest tests\test_security.py -q; pytest tests\test_desktop_smoke.py -q
Next:     If needed, extend the same pattern to backup restore/load round-trips.
