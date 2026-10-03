"""Terminal logging. Pure Python: no Streamlit import.

WHAT IS LOGGED: workflow steps, audit-log lines, LLM provider/model/timing and redacted errors.
WHAT IS NEVER LOGGED: API keys, or claim details (names, diagnosis, email text, letters).

Level: set SECURECARE_LOG_LEVEL=DEBUG|INFO|WARNING (default INFO).
"""
from __future__ import annotations

import logging
import os

_ROOT = "securecare"


def get_logger(name: str) -> logging.Logger:
    """Logger under the 'securecare' namespace; output goes to the terminal running Streamlit."""
    _setup_once()
    return logging.getLogger(f"{_ROOT}.{name}")


def _setup_once() -> None:
    root = logging.getLogger(_ROOT)
    if root.handlers:                       # Streamlit re-runs the script on every interaction
        return
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)-7s %(name)s: %(message)s", "%H:%M:%S"))
    root.addHandler(handler)
    root.setLevel(os.environ.get("SECURECARE_LOG_LEVEL", "INFO").upper())
