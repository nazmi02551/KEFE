from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient

from kefe_api.main import create_app
from kefe_api.modules.identity.account_models import OtpChannel


def _guest(client: TestClient) -> tuple[dict[str, str], str]:
    response = client.post("/v1/identity/guest")
    assert response.status_code == 201
    body = response.json()
    return {"Authorization": f"Bearer {body['access_token']}"}, body["actor_id"]


def _verification(app, client: TestClient, email: str) -> str:
    challenge = client.post(
        "/v1/auth/otp/request",
        json={"channel": "EMAIL", "identifier": email},
    )
    assert challenge.status_code == 201
    code = app.state.otp_delivery.code_for(channel=OtpChannel.EMAIL, identifier=email)
    assert code is not None
    verified = client.post(
        "/v1/auth/otp/verify",
        json={"challenge_id": challenge.json()["challenge_id"], "code": code},
    )
    assert verified.status_code == 200
    return verified.json()["verification_token"]


def test_exact_retry_with_revoked_guest_returns_identical_credential() -> None:
    app = create_app()
    client = TestClient(app)
    headers, actor_id = _guest(client)
    verification_token = _verification(app, client, "replay@example.test")
    payload = {"verification_token": verification_token}

    first = client.post("/v1/auth/guest-merge", headers=headers, json=payload)
    assert first.status_code == 200
    assert first.json()["actor_id"] == actor_id

    replay = client.post("/v1/auth/guest-merge", headers=headers, json=payload)
    assert replay.status_code == 200
    assert replay.json() == first.json()

    revoked = client.get("/v1/me/progress", headers=headers)
    assert revoked.status_code == 401
    assert revoked.json()["code"] == "AUTH_TOKEN_REVOKED"


def test_verification_replay_is_bound_to_source_actor() -> None:
    app = create_app()
    client = TestClient(app)
    owner_headers, _ = _guest(client)
    other_headers, _ = _guest(client)
    verification_token = _verification(app, client, "bound@example.test")
    payload = {"verification_token": verification_token}

    assert (
        client.post("/v1/auth/guest-merge", headers=owner_headers, json=payload).status_code
        == 200
    )
    mismatch = client.post(
        "/v1/auth/guest-merge",
        headers=other_headers,
        json=payload,
    )
    assert mismatch.status_code == 409
    assert mismatch.json()["code"] == "AUTH_MERGE_REPLAY_MISMATCH"


def test_revoked_guest_without_completed_replay_cannot_start_conversion() -> None:
    app = create_app()
    client = TestClient(app)
    headers, _ = _guest(client)
    verification_token = _verification(app, client, "revoked@example.test")

    revoked = client.delete("/v1/identity/session", headers=headers)
    assert revoked.status_code == 204
    denied = client.post(
        "/v1/auth/guest-merge",
        headers=headers,
        json={"verification_token": verification_token},
    )
    assert denied.status_code == 401
    assert denied.json()["code"] == "AUTH_TOKEN_REVOKED"


def test_concurrent_duplicate_requests_converge_to_one_replay() -> None:
    app = create_app()
    bootstrap = TestClient(app)
    headers, _ = _guest(bootstrap)
    verification_token = _verification(app, bootstrap, "concurrent@example.test")
    payload = {"verification_token": verification_token}

    def submit() -> dict[str, object]:
        with TestClient(app) as client:
            response = client.post(
                "/v1/auth/guest-merge",
                headers=headers,
                json=payload,
            )
            assert response.status_code == 200
            return response.json()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: submit(), range(2)))

    assert results[0] == results[1]
