"""DeepTutor mobile access token issuance and verification."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import logging
import os
import uuid
from typing import Any

from jose import JWTError, jwt

from deeptutor.services.auth import AUTH_SECRET, TokenPayload

logger = logging.getLogger(__name__)

_MOBILE_ALGORITHM = "HS256"
_MOBILE_ISSUER = "DeepTutorSerevr"
_MOBILE_AUDIENCE = "DeepTutorSerevr"
_DEFAULT_TTL_MINUTES = 30
_DEBUG_USER_ID = "local-admin"
_resolved_mobile_auth_secret: str | None = None


def resolve_mobile_auth_secret() -> str:
    """Return JWT signing secret for mobile tokens.

  When global auth is disabled, AUTH_SECRET may be empty. Mobile auth still
  needs a stable local secret so debug-token and WebSocket auth can work in
  local/no-auth mode.
    """
    global _resolved_mobile_auth_secret

    if AUTH_SECRET:
        return AUTH_SECRET

    env_secret = (os.getenv("DEEPTUTOR_MOBILE_AUTH_SECRET") or "").strip()
    if env_secret:
        _resolved_mobile_auth_secret = env_secret
        return env_secret

    if _resolved_mobile_auth_secret:
        return _resolved_mobile_auth_secret

    from deeptutor.multi_user.identity import load_or_create_auth_secret

    _resolved_mobile_auth_secret = load_or_create_auth_secret()
    if not _resolved_mobile_auth_secret:
        raise RuntimeError("DeepTutor auth secret is not configured")
    logger.info("mobile auth using local auth secret for token signing")
    return _resolved_mobile_auth_secret


def _mobile_settings() -> tuple[int, list[str], str, str]:
    ttl = int(os.getenv("DEEPTUTOR_MOBILE_TOKEN_TTL_MINUTES", str(_DEFAULT_TTL_MINUTES)))
    bundles = [
        item.strip()
        for item in (os.getenv("DEEPTUTOR_ALLOWED_MOBILE_BUNDLES") or "cn.zhaodk.SupportClient").split(",")
        if item.strip()
    ]
    http_base = (os.getenv("DEEPTUTOR_HTTP_BASE_URL") or "").strip().rstrip("/")
    ws_url = (os.getenv("DEEPTUTOR_WS_URL") or "").strip()
    if not ws_url and http_base:
        ws_url = http_base.replace("https://", "wss://").replace("http://", "ws://") + "/api/v1/ws"
    return ttl, bundles, http_base, ws_url


def _default_llm_selection() -> dict[str, str] | None:
    profile_id = (os.getenv("DEEPTUTOR_LLM_PROFILE_ID") or "").strip()
    model_id = (os.getenv("DEEPTUTOR_LLM_MODEL_ID") or "").strip()
    if profile_id and model_id:
        return {"profile_id": profile_id, "model_id": model_id}
    return None


def _env_flag_enabled(name: str, *, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


def _is_production_environment() -> bool:
    if _env_flag_enabled("PRODUCTION"):
        return True
    env_name = (os.getenv("DEEPTUTOR_ENV") or os.getenv("ENV") or "").strip().lower()
    return env_name in {"production", "prod", "staging"}


def is_debug_mobile_token_enabled() -> bool:
    if not _env_flag_enabled("DEEPTUTOR_MOBILE_DEBUG_TOKEN_ENABLED", default="true"):
        return False
    return not _is_production_environment()


def debug_token_availability() -> dict[str, Any]:
    env_flag = _env_flag_enabled("DEEPTUTOR_MOBILE_DEBUG_TOKEN_ENABLED", default="true")
    production_env = _is_production_environment()
    enabled = env_flag and not production_env
    if enabled:
        reason = "enabled"
    elif not env_flag:
        reason = "disabled_by_env"
    elif production_env:
        reason = "production_environment"
    else:
        reason = "disabled"
    return {
        "enabled": enabled,
        "reason": reason,
        "env_flag": env_flag,
        "production_environment": production_env,
    }


def log_debug_token_availability(*, bind: str = "") -> None:
    status = debug_token_availability()
    bind_part = f" bind={bind}" if bind else ""
    if status["enabled"]:
        logger.info(
            "mobile auth debug_token_enabled=true env=dev%s",
            bind_part,
        )
    else:
        logger.warning(
            "mobile auth debug_token availability=false reason=%s env_flag=%s production_environment=%s%s",
            status["reason"],
            status["env_flag"],
            status["production_environment"],
            bind_part,
        )


def token_hash(token: str) -> str:
    if not token:
        return "-"
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return f"sha256:{digest[:8]}"


def issue_mobile_access_token(
    *,
    user_id: str,
    client: str,
    bundle_id: str,
    device_id: str = "",
) -> tuple[str, int, dict[str, Any]]:
    auth_secret = resolve_mobile_auth_secret()

    ttl_minutes, allowed_bundles, http_base, ws_url = _mobile_settings()
    if allowed_bundles and bundle_id not in allowed_bundles:
        raise PermissionError("forbidden_bundle")

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=ttl_minutes)
    deeptutor_user_id = user_id.strip()
    if not deeptutor_user_id:
        raise ValueError("missing_user_id")

    claims = {
        "token_type": "deeptutor_mobile_access",
        "purpose": "deeptutor_ai_chat",
        "iss": _MOBILE_ISSUER,
        "aud": _MOBILE_AUDIENCE,
        "sub": deeptutor_user_id,
        "user_id": deeptutor_user_id,
        "client": client,
        "device_id": device_id,
        "bundle_id": bundle_id,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
        "jti": uuid.uuid4().hex,
    }
    token = jwt.encode(claims, auth_secret, algorithm=_MOBILE_ALGORITHM)
    if isinstance(token, bytes):
        token = token.decode("utf-8")

    data: dict[str, Any] = {
        "token": token,
        "token_type": "deeptutor_mobile_access",
        "expires_at": int(expires_at.timestamp()),
        "deeptutor_ws_url": ws_url,
        "deeptutor_http_base_url": http_base,
        "user": {
            "id": deeptutor_user_id,
        },
    }
    llm_selection = _default_llm_selection()
    if llm_selection:
        data["llm_selection"] = llm_selection
    return token, int(expires_at.timestamp()), data


def issue_debug_mobile_access_token(
    *,
    client: str,
    bundle_id: str,
    device_id: str = "",
) -> tuple[str, int, dict[str, Any]]:
    logger.info(
        "mobile auth debug_token issue_start client=%s bundle=%s device_id=%s",
        client,
        bundle_id,
        device_id or "-",
    )
    return issue_mobile_access_token(
        user_id=_DEBUG_USER_ID,
        client=client,
        bundle_id=bundle_id,
        device_id=device_id,
    )


def decode_mobile_access_token(token: str) -> TokenPayload | None:
    if not token:
        return None
    try:
        auth_secret = resolve_mobile_auth_secret()
    except RuntimeError:
        return None
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            auth_secret,
            algorithms=[_MOBILE_ALGORITHM],
            audience=_MOBILE_AUDIENCE,
            issuer=_MOBILE_ISSUER,
        )
    except JWTError:
        return None

    if payload.get("token_type") != "deeptutor_mobile_access":
        return None
    if payload.get("purpose") != "deeptutor_ai_chat":
        return None

    _, allowed_bundles, _, _ = _mobile_settings()
    bundle_id = str(payload.get("bundle_id") or "")
    if allowed_bundles and bundle_id and bundle_id not in allowed_bundles:
        return None

    user_id = str(payload.get("user_id") or payload.get("sub") or "")
    if not user_id:
        return None

    return TokenPayload(username=user_id, role="user", user_id=user_id)
