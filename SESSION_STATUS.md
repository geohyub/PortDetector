# PortDetector Session Status

Current state: PortDetector now has a local-only `--doctor` preflight on both startup surfaces (`app.py`, `main.py`) with JSON operator packet export via `--doctor-export`, including runtime path and bundled-resource proof for fresh-machine checks. The network-map layout store is now atomic on save and fail-closed on malformed JSON so broken layouts do not masquerade as valid entries.

Verification: `python -m py_compile backend\services\network_map_service.py tests\test_security.py`; `pytest tests\test_security.py tests\test_doctor.py -q`; `python app.py --doctor`; `python main.py --doctor`; `cmd /c build.bat`

Remaining risk: the doctor still uses a brief local traffic-capture probe, so administrator-only packet capture remains dependent on the live machine state at runtime. The runtime proof is still local-only and does not prove live devices, remote ports, or Windows-level restart conditions.
