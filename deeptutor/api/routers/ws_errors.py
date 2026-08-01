"""Standardized WebSocket error frames for unified_ws."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def _current_user_id() -> str:
    try:
        from deeptutor.multi_user.context import get_current_user_or_none

        user = get_current_user_or_none()
        if user is None:
            return ""
        return str(getattr(user, "user_id", "") or getattr(user, "id", "") or "")
    except Exception:
        return ""


def build_ws_error(
    *,
    content: str,
    code: str,
    reason: str,
    stage: str = "",
    recoverable: bool = False,
    session_id: str = "",
    turn_id: str = "",
    client_message_id: str = "",
    seq: int = 0,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "code": code,
        "reason": reason,
        "status": "rejected",
        "turn_terminal": True,
        "recoverable": recoverable,
    }
    if client_message_id:
        metadata["client_message_id"] = client_message_id

    return {
        "type": "error",
        "source": "unified_ws",
        "stage": stage,
        "content": content,
        "metadata": metadata,
        "session_id": session_id,
        "turn_id": turn_id,
        "seq": seq,
    }


def _client_message_id(msg: dict[str, Any]) -> str:
    return str(msg.get("client_message_id") or "").strip()


def _session_id(msg: dict[str, Any]) -> str:
    return str(msg.get("session_id") or "").strip()


def invalid_json_error() -> dict[str, Any]:
    return build_ws_error(
        content="Invalid JSON.",
        code="invalid_json",
        reason="frame_not_valid_json",
        stage="parse",
        recoverable=False,
    )


def unknown_message_type_error(msg_type: Any) -> dict[str, Any]:
    return build_ws_error(
        content=f"Unknown type: {msg_type}",
        code="unknown_message_type",
        reason="unsupported_message_type",
        stage="dispatch",
        recoverable=False,
    )


def missing_session_id_error(msg: dict[str, Any], *, stage: str) -> dict[str, Any]:
    return build_ws_error(
        content="Missing session_id.",
        code="missing_session_id",
        reason="required_field_missing",
        stage=stage,
        recoverable=False,
        session_id=_session_id(msg),
        client_message_id=_client_message_id(msg),
    )


def missing_turn_id_error(msg: dict[str, Any], *, stage: str, content: str = "Missing turn_id.") -> dict[str, Any]:
    return build_ws_error(
        content=content,
        code="missing_turn_id",
        reason="required_field_missing",
        stage=stage,
        recoverable=False,
        session_id=_session_id(msg),
        client_message_id=_client_message_id(msg),
    )


def turn_not_found_error(turn_id: str, msg: dict[str, Any], *, stage: str) -> dict[str, Any]:
    return build_ws_error(
        content=f"Turn not found: {turn_id}",
        code="turn_not_found",
        reason="turn_missing",
        stage=stage,
        recoverable=False,
        session_id=_session_id(msg),
        turn_id=turn_id,
        client_message_id=_client_message_id(msg),
    )


def map_runtime_error(exc: RuntimeError, *, stage: str, msg: dict[str, Any]) -> dict[str, Any]:
    content = str(exc)
    lowered = content.lower()
    client_message_id = _client_message_id(msg)
    session_id = _session_id(msg)

    if "invalid chat config" in lowered:
        code = "invalid_capability_config"
        reason = "invalid_chat_config"
        recoverable = False
    elif "no llm model is assigned" in lowered:
        code = "llm_model_not_assigned"
        reason = "no_available_llm_grant"
        recoverable = False
    elif "invalid llm selection" in lowered:
        code = "llm_selection_invalid"
        reason = "llm_selection_rejected"
        recoverable = False
    elif "invalid capability" in lowered or "capability config" in lowered:
        code = "invalid_capability_config"
        reason = "capability_validation_failed"
        recoverable = False
    else:
        code = "turn_rejected"
        reason = "start_turn_rejected"
        recoverable = False

    logger.warning(
        "WS %s rejected user_id=%s session_id=%s code=%s reason=%s client_message_id=%s",
        stage,
        _current_user_id(),
        session_id,
        code,
        reason,
        client_message_id,
    )

    return build_ws_error(
        content=content,
        code=code,
        reason=reason,
        stage=stage,
        recoverable=recoverable,
        session_id=session_id,
        client_message_id=client_message_id,
    )


def internal_error(exc: Exception, *, stage: str = "dispatch", msg: dict[str, Any] | None = None) -> dict[str, Any]:
    msg = msg or {}
    logger.error("Unified WS internal error at %s: %s", stage, exc, exc_info=True)
    return build_ws_error(
        content=str(exc),
        code="internal_error",
        reason="unhandled_exception",
        stage=stage,
        recoverable=True,
        session_id=_session_id(msg),
        client_message_id=_client_message_id(msg),
    )
