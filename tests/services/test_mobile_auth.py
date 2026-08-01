from datetime import datetime, timezone

import pytest

from deeptutor.services.auth import AUTH_SECRET, create_token, decode_token
from deeptutor.services.mobile_auth import (
    debug_token_availability,
    decode_mobile_access_token,
    is_debug_mobile_token_enabled,
    issue_debug_mobile_access_token,
    issue_mobile_access_token,
)


@pytest.fixture(autouse=True)
def mobile_env(monkeypatch):
    monkeypatch.setenv("DEEPTUTOR_HTTP_BASE_URL", "http://127.0.0.1:9898")
    monkeypatch.setenv("DEEPTUTOR_WS_URL", "ws://127.0.0.1:9898/api/v1/ws")
    monkeypatch.setenv("DEEPTUTOR_ALLOWED_MOBILE_BUNDLES", "cn.zhaodk.SupportClient")
    monkeypatch.delenv("DEEPTUTOR_MOBILE_DEBUG_TOKEN_ENABLED", raising=False)
    monkeypatch.delenv("DEEPTUTOR_ENV", raising=False)
    monkeypatch.delenv("ENV", raising=False)
    monkeypatch.delenv("PRODUCTION", raising=False)


def test_issue_and_decode_mobile_access_token(monkeypatch):
    if not AUTH_SECRET:
        create_token("local-admin", role="admin", user_id="local-admin")
        monkeypatch.setattr("deeptutor.services.mobile_auth.AUTH_SECRET", AUTH_SECRET or "test-secret")
    token, expires_at, data = issue_mobile_access_token(
        user_id="local-admin",
        client="ios",
        bundle_id="cn.zhaodk.SupportClient",
    )
    assert data["token_type"] == "deeptutor_mobile_access"
    assert expires_at > int(datetime.now(timezone.utc).timestamp())

    payload = decode_mobile_access_token(token)
    assert payload is not None
    assert payload.user_id == "local-admin"

    decoded = decode_token(token)
    assert decoded is not None
    assert decoded.user_id == "local-admin"


def test_issue_debug_mobile_access_token(monkeypatch):
    if not AUTH_SECRET:
        monkeypatch.setattr("deeptutor.services.mobile_auth.AUTH_SECRET", "test-secret")
    token, _, data = issue_debug_mobile_access_token(
        client="ios",
        bundle_id="cn.zhaodk.SupportClient",
        device_id="debug-device",
    )
    assert token
    assert data["user"]["id"] == "local-admin"


def test_debug_token_enabled_by_default(monkeypatch):
    assert is_debug_mobile_token_enabled() is True
    status = debug_token_availability()
    assert status["enabled"] is True
    assert status["reason"] == "enabled"


def test_debug_token_explicit_disable(monkeypatch):
    monkeypatch.setenv("DEEPTUTOR_MOBILE_DEBUG_TOKEN_ENABLED", "false")
    assert is_debug_mobile_token_enabled() is False
    status = debug_token_availability()
    assert status["enabled"] is False
    assert status["reason"] == "disabled_by_env"


def test_debug_token_disabled_in_production(monkeypatch):
    monkeypatch.setenv("DEEPTUTOR_ENV", "production")
    assert is_debug_mobile_token_enabled() is False
    status = debug_token_availability()
    assert status["reason"] == "production_environment"


def test_issue_mobile_token_without_global_auth_secret(monkeypatch):
    monkeypatch.setattr("deeptutor.services.mobile_auth.AUTH_SECRET", "")
    monkeypatch.setattr("deeptutor.services.mobile_auth._resolved_mobile_auth_secret", None)
    monkeypatch.setattr(
        "deeptutor.multi_user.identity.load_or_create_auth_secret",
        lambda: "generated-local-secret",
    )

    token, _, data = issue_mobile_access_token(
        user_id="local-admin",
        client="ios",
        bundle_id="cn.zhaodk.SupportClient",
    )
    assert token
    assert data["token_type"] == "deeptutor_mobile_access"
    payload = decode_mobile_access_token(token)
    assert payload is not None
    assert payload.user_id == "local-admin"
