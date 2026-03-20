"""Ping service using subprocess for Windows compatibility (no admin required)."""

import re
import subprocess
from typing import Optional, Tuple


def ping(ip: str, timeout_ms: int = 1000) -> Tuple[bool, Optional[int]]:
    """Ping an IP address. Returns (success, rtt_ms)."""
    try:
        result = subprocess.run(
            ["ping", "-n", "1", "-w", str(timeout_ms), ip],
            capture_output=True,
            text=True,
            timeout=timeout_ms / 1000 + 2,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if result.returncode == 0:
            match = re.search(r'time[=<](\d+)\s*ms', result.stdout, re.IGNORECASE)
            if match:
                rtt = int(match.group(1))
                return True, rtt
            # Some locales use different format
            match = re.search(r'=\s*(\d+)\s*ms', result.stdout)
            if match:
                rtt = int(match.group(1))
                return True, rtt
            return True, 0
        return False, None
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False, None
