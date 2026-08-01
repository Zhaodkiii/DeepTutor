"""Bridge token verification for SparkService-issued AI chat credentials."""

from __future__ import annotations

import os
from typing import Any

from jose import JWTError, jwt

from deeptutor.services.auth import TokenPayload

_BRIDGE_ALGORITHM = "HS256"


def _bridge_settings() -> tuple[str, str, str, list[str]]:
    secret = (os.getenv("DEEPTUTOR_BRIDGE_JWT_SECRET") or "").strip()
    issuer = (os.getenv("DEEPTUTOR_ALLOWED_BRIDGE_ISSUER") or "SparkService").strip()
    audience = (os.getenv("DEEPTUTOR_BRIDGE_AUDIENCE") or "DeepTutorSerevr").strip()
    bundles = [
        item.strip()
        for item in (os.getenv("DEEPTUTOR_ALLOWED_BRIDGE_BUNDLES") or "cn.zhaodk.SupportClient").split(",")
        if item.strip()
    ]
    return secret, issuer, audience, bundles


def decode_bridge_token(token: str) -> TokenPayload | None:
    """Validate a SparkService-issued bridge JWT and map it to DeepTutor user context."""
    secret, issuer, audience, allowed_bundles = _bridge_settings()
    if not token or not secret:
        return None

    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            secret,
            algorithms=[_BRIDGE_ALGORITHM],
            audience=audience,
            issuer=issuer,
        )
    except JWTError:
        return None

    if payload.get("token_type") != "deeptutor_bridge":
        return None
    if payload.get("purpose") != "deeptutor_ai_chat":
        return None
    if payload.get("client") != "ios":
        return None

    bundle_id = str(payload.get("bundle_id") or "")
    if allowed_bundles and bundle_id not in allowed_bundles:
        return None

    user_id = str(payload.get("user_id") or payload.get("sub") or "")
    if not user_id:
        return None

    return TokenPayload(
        username=f"spark:{user_id}",
        role="user",
        user_id=user_id,
    )
