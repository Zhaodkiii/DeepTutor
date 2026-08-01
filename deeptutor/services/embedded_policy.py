"""SparkService embedded-mode capability policy.

Preserves DeepTutor's full product surface when running inside SparkService.
Security-sensitive knobs (exec, PocketBase) remain env-controlled; everything
else follows DeepTutor defaults unless explicitly disabled.
"""

from __future__ import annotations

import os


def embedded_mode() -> bool:
    return os.getenv("DEEPTUTOR_EMBEDDED", "false").lower() in ("1", "true", "yes", "y")


def preserve_full_capabilities() -> bool:
    if not embedded_mode():
        return False
    return os.getenv("DEEPTUTOR_PRESERVE_FULL_CAPABILITIES", "true").lower() in (
        "1",
        "true",
        "yes",
        "y",
    )


def partner_channels_allowed() -> bool:
    if not embedded_mode():
        return True
    return os.getenv("DEEPTUTOR_ALLOW_PARTNER_CHANNELS", "true").lower() in (
        "1",
        "true",
        "yes",
        "y",
    )


def exec_tools_allowed() -> bool:
    if not embedded_mode():
        return True
    return os.getenv("DEEPTUTOR_ALLOW_EXEC_TOOLS", "false").lower() in (
        "1",
        "true",
        "yes",
        "y",
    )


def pocketbase_allowed() -> bool:
    if not embedded_mode():
        return True
    return os.getenv("DEEPTUTOR_ALLOW_POCKETBASE", "false").lower() in (
        "1",
        "true",
        "yes",
        "y",
    )


__all__ = [
    "embedded_mode",
    "exec_tools_allowed",
    "partner_channels_allowed",
    "pocketbase_allowed",
    "preserve_full_capabilities",
]
