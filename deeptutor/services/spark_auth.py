"""SparkService JWT bridge for embedded DeepTutor runtime."""

from __future__ import annotations

import logging
import os

import jwt

from deeptutor.services.auth import TokenPayload

logger = logging.getLogger(__name__)

SPARK_AUTH_ENABLED = os.getenv("DEEPTUTOR_SPARK_AUTH_ENABLED", "false").lower() in (
    "1",
    "true",
    "yes",
    "y",
)
SPARK_JWT_SIGNING_KEY = os.getenv("SPARK_JWT_SIGNING_KEY", "")
SPARK_JWT_ALGORITHM = "HS256"


def spark_auth_enabled() -> bool:
    return SPARK_AUTH_ENABLED and bool(SPARK_JWT_SIGNING_KEY)


def decode_spark_token(token: str | None) -> TokenPayload | None:
    if not spark_auth_enabled() or not token:
        return None

    try:
        claims = jwt.decode(
            token,
            SPARK_JWT_SIGNING_KEY,
            algorithms=[SPARK_JWT_ALGORITHM],
            options={"verify_aud": False},
        )
    except jwt.PyJWTError as exc:
        logger.debug("Spark JWT decode failed: %s", exc)
        return None

    user_id = str(claims.get("user_id") or claims.get("sub") or "")
    if not user_id:
        return None

    username = str(claims.get("username") or user_id)
    role = "user"

    try:
        from django.contrib.auth import get_user_model

        user = (
            get_user_model()
            .objects.filter(id=int(user_id))
            .only("id", "username", "is_staff", "is_superuser", "is_active")
            .first()
        )
        if user is None or not user.is_active:
            return None
        username = str(user.username or user.id)
        role = "admin" if user.is_staff or user.is_superuser else "user"
    except Exception:
        logger.debug("Spark JWT user lookup unavailable; using token claims only")

    return TokenPayload(username=username, role=role, user_id=user_id)
