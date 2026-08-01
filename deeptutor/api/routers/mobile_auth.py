"""Mobile client auth endpoints — independent from SparkService."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, Field

from deeptutor.services.mobile_auth import (
    debug_token_availability,
    decode_mobile_access_token,
    issue_debug_mobile_access_token,
    issue_mobile_access_token,
    token_hash,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class MobileTokenRequest(BaseModel):
    client: str = Field(default="ios")
    app_bundle: str
    purpose: str = Field(default="deeptutor_ai_chat")
    device_id: str | None = None


def _validate_request(body: MobileTokenRequest) -> None:
    if body.purpose != "deeptutor_ai_chat":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_purpose")
    if body.client != "ios":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_client")


def _issue_response(
    *,
    user_id: str,
    client: str,
    bundle_id: str,
    device_id: str,
    source: str,
) -> dict:
    try:
        _, _, data = issue_mobile_access_token(
            user_id=user_id,
            client=client,
            bundle_id=bundle_id,
            device_id=device_id,
        )
    except PermissionError:
        logger.warning(
            "mobile auth rejected reason=forbidden_bundle source=%s bundle=%s",
            source,
            bundle_id,
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden_bundle") from None
    except RuntimeError as exc:
        logger.error("mobile auth token issue failed source=%s error=%s", source, exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="token_issue_failed") from exc

    logger.info(
        "mobile auth token issued source=%s user_id=%s client=%s bundle=%s",
        source,
        user_id,
        client,
        bundle_id,
    )
    return {"code": 0, "msg": "ok", "data": data}


@router.post("/debug-token")
async def issue_debug_mobile_token(body: MobileTokenRequest):
    _validate_request(body)
    availability = debug_token_availability()
    if not availability["enabled"]:
        logger.warning(
            "mobile auth debug_token rejected reason=%s env_flag=%s production_environment=%s bundle=%s",
            availability["reason"],
            availability["env_flag"],
            availability["production_environment"],
            body.app_bundle,
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="debug_token_disabled")

    logger.info(
        "mobile auth debug_token issue_start enabled=true env=debug bundle=%s client=%s",
        body.app_bundle,
        body.client,
    )
    try:
        _, _, data = issue_debug_mobile_access_token(
            client=body.client,
            bundle_id=body.app_bundle,
            device_id=str(body.device_id or ""),
        )
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden_bundle") from None
    except RuntimeError as exc:
        logger.error("mobile auth debug_token issue failed error=%s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="token_issue_failed") from exc
    logger.info(
        "mobile auth debug_token issued user_id=%s client=%s bundle=%s",
        data.get("user", {}).get("id", "-"),
        body.client,
        body.app_bundle,
    )
    return {"code": 0, "msg": "ok", "data": data}


@router.post("/refresh")
async def refresh_mobile_token(
    body: MobileTokenRequest,
    authorization: str | None = Header(default=None),
):
    _validate_request(body)

    if not authorization or not authorization.lower().startswith("bearer "):
        logger.warning("mobile auth refresh rejected reason=missing_authorization")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing_authorization")

    deeptutor_token = authorization.split(" ", 1)[1].strip()
    payload = decode_mobile_access_token(deeptutor_token)
    if payload is None:
        logger.warning(
            "mobile auth refresh rejected reason=invalid_deeptutor_token token_hash=%s",
            token_hash(deeptutor_token),
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_deeptutor_token")

    return _issue_response(
        user_id=payload.user_id,
        client=body.client,
        bundle_id=body.app_bundle,
        device_id=str(body.device_id or ""),
        source="refresh",
    )
