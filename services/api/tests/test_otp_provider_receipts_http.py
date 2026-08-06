from __future__ import annotations

import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient

from kefe_api.core.settings import get_settings
from kefe_api.main import create_app

_SECRET = "http-receipt-secret-material-at-least-32-bytes"
_KEY_ID = "http-v1"
_PATH = "/internal/provider/v1/otp-delivery-receipts"


def _client(monkeypatch) -> TestClient:
    monkeypatch.setenv("KEFE_ENVIRONMENT", "development")
    monkeypatch.setenv("KEFE_PERSISTENCE_BACKEND", "memory")
    monkeypatch.setenv("KEFE_OTP_RECEIPT_MODE", "HMAC_SHA256")
    monkeypatch.setenv(
        "KEFE_OTP_RECEIPT_SECRET_REFS",
        json.dumps({_KEY_ID: "envref://KEFE_TEST_OTP_RECEIPT_SECRET"}),
    )
    monkeypatch.setenv("KEFE_TEST_OTP_RECEIPT_SECRET", _SECRET)
    get_settings.cache_clear()
    return TestClient(create_app())


def _signed_request(*, now: datetime, event_id: str, outcome: str = "DELIVERED"):
    delivery_id = uuid4()
    occurred_at = now - timedelta(seconds=5)
    raw = json.dumps(
        {
            "delivery_id": str(delivery_id),
            "occurred_at": occurred_at.isoformat(),
            "outcome": outcome,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    timestamp = str(int(now.timestamp()))
    canonical = (
        b"v1\n"
        + timestamp.encode("ascii")
        + b"\n"
        + _KEY_ID.encode("ascii")
        + b"\n"
        + event_id.encode("ascii")
        + b"\n"
        + raw
    )
    signature = hmac.new(
        _SECRET.encode("ascii"),
        canonical,
        hashlib.sha256,
    ).hexdigest()
    headers = {
        "content-type": "application/json",
        "X-KEFE-OTP-Receipt-Timestamp": timestamp,
        "X-KEFE-OTP-Receipt-Key-Id": _KEY_ID,
        "X-KEFE-OTP-Receipt-Event-Id": event_id,
        "X-KEFE-OTP-Receipt-Signature": signature,
    }
    return raw, headers


def test_signed_callback_is_accepted_and_exact_replay_is_duplicate(monkeypatch) -> None:
    client = _client(monkeypatch)
    now = datetime.now(UTC)
    raw, headers = _signed_request(
        now=now,
        event_id="evt_01J9K5R4X2Y7Z8A9B0C1D2E401",
    )

    first = client.post(_PATH, content=raw, headers=headers)
    second = client.post(_PATH, content=raw, headers=headers)

    assert first.status_code == 202
    assert first.json() == {"accepted": True, "duplicate": False}
    assert second.status_code == 202
    assert second.json() == {"accepted": True, "duplicate": True}
    facts = client.app.state.otp_provider_receipt_service.facts(
        window=timedelta(hours=1)
    )
    assert facts.total_count == 1
    assert facts.delivered_count == 1


def test_callback_auth_failure_is_generic_and_consumer_openapi_is_unchanged(monkeypatch) -> None:
    client = _client(monkeypatch)
    raw, headers = _signed_request(
        now=datetime.now(UTC),
        event_id="evt_01J9K5R4X2Y7Z8A9B0C1D2E402",
    )
    headers["X-KEFE-OTP-Receipt-Signature"] = "0" * 64

    response = client.post(_PATH, content=raw, headers=headers)

    assert response.status_code == 401
    assert response.json()["code"] == "AUTH_OTP_RECEIPT_REJECTED"
    assert _PATH not in client.get("/openapi.json").json()["paths"]


def test_malformed_and_oversized_bodies_are_rejected_before_schema_detail_leaks(
    monkeypatch,
) -> None:
    client = _client(monkeypatch)
    _, headers = _signed_request(
        now=datetime.now(UTC),
        event_id="evt_01J9K5R4X2Y7Z8A9B0C1D2E404",
    )

    for raw in (b"{", b"{" + b"x" * 4_097):
        response = client.post(_PATH, content=raw, headers=headers)
        assert response.status_code == 401
        assert response.json()["code"] == "AUTH_OTP_RECEIPT_REJECTED"
        assert "detail" not in response.json()

    facts = client.app.state.otp_provider_receipt_service.facts(
        window=timedelta(hours=1)
    )
    assert facts.total_count == 0


def test_disabled_callback_returns_not_found_without_receipt_configuration(monkeypatch) -> None:
    monkeypatch.setenv("KEFE_ENVIRONMENT", "development")
    monkeypatch.setenv("KEFE_PERSISTENCE_BACKEND", "memory")
    monkeypatch.setenv("KEFE_OTP_RECEIPT_MODE", "DISABLED")
    monkeypatch.delenv("KEFE_OTP_RECEIPT_SECRET_REFS", raising=False)
    get_settings.cache_clear()
    client = TestClient(create_app())
    now = datetime.now(UTC)
    raw = json.dumps(
        {
            "delivery_id": str(uuid4()),
            "occurred_at": now.isoformat(),
            "outcome": "DELIVERED",
        },
        separators=(",", ":"),
    ).encode("utf-8")
    response = client.post(
        _PATH,
        content=raw,
        headers={
            "content-type": "application/json",
            "X-KEFE-OTP-Receipt-Timestamp": str(int(now.timestamp())),
            "X-KEFE-OTP-Receipt-Key-Id": _KEY_ID,
            "X-KEFE-OTP-Receipt-Event-Id": "evt_01J9K5R4X2Y7Z8A9B0C1D2E403",
            "X-KEFE-OTP-Receipt-Signature": "0" * 64,
        },
    )

    assert response.status_code == 404
    assert response.json()["code"] == "AUTH_OTP_RECEIPT_DISABLED"
