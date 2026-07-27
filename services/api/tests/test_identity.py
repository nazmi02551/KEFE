from __future__ import annotations

from fastapi.testclient import TestClient

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
    client = TestClient(create_app())
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
