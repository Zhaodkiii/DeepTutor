from datetime import datetime, timedelta, timezone

import jwt
import pytest

from deeptutor.logging.formatters import redact_sensitive
from deeptutor.services.bridge_auth import decode_bridge_token


@pytest.fixture(autouse=True)
def bridge_env(monkeypatch):
    monkeypatch.setenv("DEEPTUTOR_BRIDGE_JWT_SECRET", "test-bridge-secret")
    monkeypatch.setenv("DEEPTUTOR_ALLOWED_BRIDGE_BUNDLES", "cn.zhaodk.SupportClient")
    monkeypatch.setenv("DEEPTUTOR_ALLOWED_BRIDGE_ISSUER", "SparkService")
    monkeypatch.setenv("DEEPTUTOR_BRIDGE_AUDIENCE", "DeepTutorSerevr")


def _make_bridge_token(**overrides):
    now = datetime.now(timezone.utc)
    payload = {
        "token_type": "deeptutor_bridge",
        "purpose": "deeptutor_ai_chat",
        "iss": "SparkService",
        "aud": "DeepTutorSerevr",
        "sub": "42",
        "user_id": "42",
        "client": "ios",
        "device_id": "debug-device",
        "bundle_id": "cn.zhaodk.SupportClient",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=10)).timestamp()),
        "jti": "test-jti",
    }
    payload.update(overrides)
    return jwt.encode(payload, "test-bridge-secret", algorithm="HS256")


def test_decode_bridge_token_accepts_valid_token():
    token = _make_bridge_token()
    payload = decode_bridge_token(token)
    assert payload is not None
    assert payload.user_id == "42"
    assert payload.username == "spark:42"


def test_decode_bridge_token_rejects_wrong_audience():
    token = _make_bridge_token(aud="OtherService")
    assert decode_bridge_token(token) is None


def test_decode_bridge_token_rejects_wrong_purpose():
    token = _make_bridge_token(purpose="other")
    assert decode_bridge_token(token) is None


def test_decode_bridge_token_rejects_forbidden_bundle():
    token = _make_bridge_token(bundle_id="com.example.other")
    assert decode_bridge_token(token) is None


def test_redact_sensitive_masks_query_token():
    raw = 'WebSocket /api/v1/ws?token=eyJhbGciOiJIUzI1NiJ9.payload.signature [accepted]'
    redacted = redact_sensitive(raw)
    assert "eyJhbGci" not in redacted
    assert "token=<redacted>" in redacted
