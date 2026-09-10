from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from kefe_api.core.settings import get_settings
from kefe_api.main import create_app
from kefe_api.modules.decision.bootstrap import DEMO_CASE_ID


def test_guest_credential_allows_authenticated_write() -> None:
    client = TestClient(create_app())
    guest = client.post("/v1/identity/guest")
    assert guest.status_code == 201
    body = guest.json()
    assert body["token_type"] == "Bearer"
    assert body["access_token"].startswith("kefe_g_")

    response = client.post(
        f"/v1/cases/{DEMO_CASE_ID}/weigh-sessions",
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )
    assert response.status_code == 201


def test_invalid_bearer_is_rejected() -> None:
    from kefe_api.modules.identity.in_memory import InMemoryIdentityRepository
    from kefe_api.modules.identity.service import IdentityService

    # Override the identity repository with dev_auto_session=False to ensure
    # unknown bearer tokens are rejected with 401 (not auto-admitted as dev guests).
    app = create_app()
    strict_repo = InMemoryIdentityRepository(allow_dev_auto_session=False)
    settings = get_settings()
    app.state.identity_repository = strict_repo
    app.state.identity_service = IdentityService(
        repository=strict_repo,
        guest_token_ttl_days=settings.guest_token_ttl_days,
    )

    client = TestClient(app)
    response = client.post(
        f"/v1/cases/{DEMO_CASE_ID}/weigh-sessions",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert response.status_code == 401
    assert response.json()["code"] == "AUTH_TOKEN_INVALID"


def test_guest_session_can_be_revoked() -> None:
    client = TestClient(create_app())
    guest = client.post("/v1/identity/guest").json()
    headers = {"Authorization": f"Bearer {guest['access_token']}"}

    assert client.delete("/v1/identity/session", headers=headers).status_code == 204
    denied = client.post(
        f"/v1/cases/{DEMO_CASE_ID}/weigh-sessions",
        headers=headers,
    )
    assert denied.status_code == 401
    assert denied.json()["code"] == "AUTH_TOKEN_REVOKED"


def test_guest_endpoint_rate_limits_issuance(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KEFE_GUEST_ISSUE_RATE_LIMIT", "2")
    monkeypatch.setenv("KEFE_GUEST_ISSUE_RATE_WINDOW_SECONDS", "60")
    get_settings.cache_clear()
    try:
        client = TestClient(create_app())
        assert client.post("/v1/identity/guest").status_code == 201
        assert client.post("/v1/identity/guest").status_code == 201

        blocked = client.post("/v1/identity/guest")
        assert blocked.status_code == 429
        assert blocked.json()["code"] == "AUTH_GUEST_RATE_LIMITED"
        assert blocked.json()["retryable"] is True
    finally:
        get_settings.cache_clear()


def test_required_device_integrity_blocks_unconfigured_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("KEFE_DEVICE_INTEGRITY_MODE", "REQUIRED")
    get_settings.cache_clear()
    try:
        client = TestClient(create_app())
        blocked = client.post(
            "/v1/identity/guest",
            json={"platform": "ANDROID", "integrity_evidence": "opaque"},
        )
        assert blocked.status_code == 403
        assert blocked.json()["code"] == "AUTH_DEVICE_INTEGRITY_REQUIRED"
    finally:
        get_settings.cache_clear()
