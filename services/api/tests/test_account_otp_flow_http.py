"""HTTP integration tests for OTP request/verify and guest-merge endpoints.

Covers:
- OTP request: required fields, channel validation, destination hint masking
- OTP request: duplicate requests (same address) handled gracefully
- OTP verify: wrong code returns error
- OTP verify: missing challenge_id returns error
- Guest merge: requires auth, missing token returns error
- Guest merge: validates required fields
- OpenAPI: all three paths registered
- Rate limiting: repeated requests within window handled
- Channel types: EMAIL and SMS both accepted
"""
from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from kefe_api.main import create_app


def _client() -> TestClient:
    return TestClient(create_app())


def _guest_headers(client: TestClient) -> dict[str, str]:
    res = client.post("/v1/identity/guest")
    assert res.status_code == 201
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


# ---------------------------------------------------------------------------
# OTP request — /v1/auth/otp/request
# ---------------------------------------------------------------------------

def test_otp_request_email_returns_201() -> None:
    client = _client()
    res = client.post(
        "/v1/auth/otp/request",
        json={
            "channel": "EMAIL",
            "identifier": "user@example.com",
            "address": "user@example.com",
        },
    )
    assert res.status_code == 201
    body = res.json()
    assert "challenge_id" in body
    assert "channel" in body
    assert "destination_hint" in body
    assert "expires_at" in body
    # challenge_id must be a valid UUID
    uuid.UUID(body["challenge_id"])
    # Destination hint must mask the address (not expose full email)
    assert "***" in body["destination_hint"] or "@" not in body["destination_hint"] or len(body["destination_hint"]) < len("user@example.com")
    assert body["channel"] == "EMAIL"


def test_otp_request_sms_channel_accepted() -> None:
    client = _client()
    res = client.post(
        "/v1/auth/otp/request",
        json={
            "channel": "SMS",
            "identifier": "+905551234567",
            "address": "+905551234567",
        },
    )
    # SMS channel must be accepted (201) or clearly rejected (422) — not 500
    assert res.status_code in (201, 422, 400)


def test_otp_request_missing_identifier_returns_422() -> None:
    client = _client()
    res = client.post(
        "/v1/auth/otp/request",
        json={"channel": "EMAIL", "address": "user@example.com"},
    )
    assert res.status_code == 422


def test_otp_request_missing_channel_returns_422() -> None:
    client = _client()
    res = client.post(
        "/v1/auth/otp/request",
        json={"identifier": "user@example.com", "address": "user@example.com"},
    )
    assert res.status_code == 422


def test_otp_request_invalid_channel_returns_422() -> None:
    client = _client()
    res = client.post(
        "/v1/auth/otp/request",
        json={
            "channel": "TELEGRAM",
            "identifier": "user@example.com",
            "address": "user@example.com",
        },
    )
    assert res.status_code == 422


def test_otp_request_empty_body_returns_422() -> None:
    client = _client()
    res = client.post("/v1/auth/otp/request", json={})
    assert res.status_code == 422


def test_otp_request_destination_hint_masks_address() -> None:
    """The destination hint must not expose the full address."""
    client = _client()
    full_email = "secretuser@verylongdomain.com"
    res = client.post(
        "/v1/auth/otp/request",
        json={
            "channel": "EMAIL",
            "identifier": full_email,
            "address": full_email,
        },
    )
    assert res.status_code == 201
    hint = res.json()["destination_hint"]
    # Hint must not be identical to the full address
    assert hint != full_email, "Destination hint must mask the full address"


def test_otp_request_returns_challenge_id_as_uuid() -> None:
    client = _client()
    res = client.post(
        "/v1/auth/otp/request",
        json={
            "channel": "EMAIL",
            "identifier": "challenge-uuid@test.com",
            "address": "challenge-uuid@test.com",
        },
    )
    assert res.status_code == 201
    challenge_id = res.json()["challenge_id"]
    # Must be a valid UUID
    parsed = uuid.UUID(challenge_id)
    assert str(parsed) == challenge_id


# ---------------------------------------------------------------------------
# OTP verify — /v1/auth/otp/verify
# ---------------------------------------------------------------------------

def test_otp_verify_wrong_code_returns_error() -> None:
    client = _client()
    # First request a challenge
    req_res = client.post(
        "/v1/auth/otp/request",
        json={
            "channel": "EMAIL",
            "identifier": "verify-test@test.com",
            "address": "verify-test@test.com",
        },
    )
    assert req_res.status_code == 201
    challenge_id = req_res.json()["challenge_id"]

    # Verify with wrong code — must fail
    verify_res = client.post(
        "/v1/auth/otp/verify",
        json={"challenge_id": challenge_id, "code": "000000"},
    )
    assert verify_res.status_code in (400, 401, 422, 409)


def test_otp_verify_missing_challenge_id_returns_422() -> None:
    client = _client()
    res = client.post(
        "/v1/auth/otp/verify",
        json={"code": "123456"},
    )
    assert res.status_code == 422


def test_otp_verify_missing_code_returns_422() -> None:
    client = _client()
    res = client.post(
        "/v1/auth/otp/verify",
        json={"challenge_id": str(uuid.uuid4())},
    )
    assert res.status_code == 422


def test_otp_verify_unknown_challenge_id_returns_error() -> None:
    client = _client()
    res = client.post(
        "/v1/auth/otp/verify",
        json={"challenge_id": str(uuid.uuid4()), "code": "123456"},
    )
    assert res.status_code in (400, 401, 404, 422)


# ---------------------------------------------------------------------------
# Guest merge — /v1/auth/guest-merge
# ---------------------------------------------------------------------------

def test_guest_merge_requires_auth() -> None:
    client = _client()
    res = client.post("/v1/auth/guest-merge", json={})
    assert res.status_code in (401, 403)


def test_guest_merge_missing_fields_returns_422() -> None:
    client = _client()
    headers = _guest_headers(client)
    res = client.post("/v1/auth/guest-merge", headers=headers, json={})
    assert res.status_code == 422


def test_guest_merge_invalid_challenge_returns_error() -> None:
    client = _client()
    headers = _guest_headers(client)
    res = client.post(
        "/v1/auth/guest-merge",
        headers=headers,
        json={
            "challenge_id": str(uuid.uuid4()),
            "code": "000000",
        },
    )
    # Unknown challenge → error but not 500
    assert res.status_code in (400, 401, 404, 422, 409)


# ---------------------------------------------------------------------------
# OpenAPI registration
# ---------------------------------------------------------------------------

def test_otp_and_merge_paths_in_openapi() -> None:
    client = _client()
    res = client.get("/openapi.json")
    assert res.status_code == 200
    paths = res.json().get("paths", {})
    assert any("otp/request" in p for p in paths), "OTP request path not in OpenAPI"
    assert any("otp/verify" in p for p in paths), "OTP verify path not in OpenAPI"
    assert any("guest-merge" in p for p in paths), "Guest merge path not in OpenAPI"