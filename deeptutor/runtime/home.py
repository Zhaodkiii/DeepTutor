"""Runtime home resolution for installed and source DeepTutor runs."""

from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

DEEPTUTOR_HOME_ENV = "DEEPTUTOR_HOME"
EMBEDDED_ENV = "DEEPTUTOR_EMBEDDED"
STRICT_HOME_ENV = "DEEPTUTOR_STRICT_HOME"
PACKAGE_ROOT = Path(__file__).resolve().parents[2]


def _embedded_mode() -> bool:
    return os.getenv(EMBEDDED_ENV, "false").lower() in ("1", "true", "yes", "y")


def _strict_home() -> bool:
    return os.getenv(STRICT_HOME_ENV, "false").lower() in ("1", "true", "yes", "y")


def get_runtime_home(home: str | Path | None = None) -> Path:
    """Return the directory that owns runtime data for this process.

    Priority:
    1. Explicit *home* argument.
    2. ``DEEPTUTOR_HOME`` environment variable.
    3. Current working directory (standalone mode only).

    The returned path is the workspace root; runtime data lives below
    ``<home>/data``.
    """

    raw = home if home is not None else os.getenv(DEEPTUTOR_HOME_ENV)
    if raw is None or str(raw).strip() == "":
        if _embedded_mode() or _strict_home():
            raise RuntimeError(
                f"{DEEPTUTOR_HOME_ENV} must be set when DeepTutor runs inside SparkService"
            )
        return Path.cwd().resolve()
    return Path(raw).expanduser().resolve()


def get_runtime_data_root(home: str | Path | None = None) -> Path:
    """Return ``<runtime-home>/data``."""

    return get_runtime_home(home) / "data"


__all__ = [
    "DEEPTUTOR_HOME_ENV",
    "PACKAGE_ROOT",
    "get_runtime_home",
    "get_runtime_data_root",
]
