"""PortDetector application constants and local security helpers."""

from __future__ import annotations

import os
import secrets
from pathlib import Path

VERSION = "2.0.0"
APP_NAME = "PortDetector"
DEFAULT_WEB_PORT = 5555
DEFAULT_PING_INTERVAL = 5  # seconds
DEFAULT_INTERFACE_POLL_INTERVAL = 3  # seconds
DEFAULT_DELAY_THRESHOLD_MS = 200
DEFAULT_SCAN_TIMEOUT = 1  # seconds per port
MAX_LOG_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_LOG_BACKUPS = 2
MAX_CONFIG_BACKUPS = 20
SECRET_KEY_ENV_VAR = "PORTDETECTOR_SECRET_KEY"
SECRET_KEY_FILENAME = "portdetector.secret"


def load_or_create_secret_key(data_dir: str, *, env_var: str = SECRET_KEY_ENV_VAR,
                              filename: str = SECRET_KEY_FILENAME) -> str:
    """Load a persistent local secret key or create one if missing.

    The explicit env var keeps deployment overrides simple, while the on-disk
    fallback removes the hardcoded development secret and keeps sessions stable
    across restarts for the local app.
    """

    env_value = os.environ.get(env_var, "").strip()
    if env_value:
        return env_value

    path = Path(data_dir) / filename
    if path.exists():
        value = path.read_text(encoding="utf-8").strip()
        if value:
            return value

    path.parent.mkdir(parents=True, exist_ok=True)
    value = secrets.token_urlsafe(48)
    path.write_text(value, encoding="utf-8")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    return value
