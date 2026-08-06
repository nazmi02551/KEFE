from __future__ import annotations

import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from kefe_api.core.errors import DomainError
from kefe_api.modules.identity.otp_provider_receipts import (
    InMemoryOtpProviderReceiptRepository,
    OtpProviderReceiptOutcome,
    OtpProviderReceiptPolicy,
    OtpProviderReceiptService,
)
from kefe_api.modules.knowledge.provider_secret_execution import SecretLease

_SECRET = b"receipt-secret-material-that-is-at-least-32-bytes"
_KEY_ID = "receipt-v1"


class StaticResolver:
    def resolve(self, *, key_id: str, at: datetime) -> SecretLease:
        if key_id != _KEY_ID:
            raise ValueError("unknown key")
        return SecretLease(_SECRET, expires_at=at + timedelta(seconds=30))


def _service(
    repository: InMemoryOtpProviderReceiptRepository | None = None,
) -> OtpProviderReceiptService:
    return OtpProviderReceiptService(
        repository=repository or InMemoryOtpProviderReceiptRepository(),
        secret_resolver=StaticResolver(),
        policy=OtpProviderReceiptPolicy(),
        enabled=True,
    )


def _body(*, delivery_id, outcome: str, occurred_at: datetime) -> bytes:
    return json.dumps(
        {
            "delivery_id": str(delivery_id),
            "outcome": outcome,
            "occurred_at": occurred_at.isoformat(),
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _signature(
    *,
    raw_body: bytes,
    timestamp: str,
    event_id: str,
    key_id: str = _KEY_ID,
) -> str:
    canonical = (
        b"v1\n"
        + timestamp.encode("ascii")
        + b"\n"
        + key_id.encode("ascii")
        + b"\n"
        + event_id.encode("ascii")
        + b"\n"
        + raw_body
    )
    return hmac.new(_SECRET, canonical, hashlib.sha256).hexdigest()


def test_valid_receipt_is_authenticated_and_persisted_aggregate_only() -> None:
    repository = InMemoryOtpProviderReceiptRepository()
    service = _service(repository)
    now = datetime(2026, 8, 6, 5, 0, tzinfo=UTC)
    delivery_id = uuid4()
    event_id = "evt_01J9K5R4X2Y7Z8A9B0C1D2E3FA"
    occurred_at = now - timedelta(seconds=10)
    raw = _body(
        delivery_id=delivery_id,
        outcome="DELIVERED",
        occurred_at=occurred_at,
    )
    timestamp = str(int(now.timestamp()))

    result = service.receive(
        raw_body=raw,
        timestamp=timestamp,
        key_id=_KEY_ID,
        provider_event_id=event_id,
        signature=_signature(
            raw_body=raw,
            timestamp=timestamp,
            event_id=event_id,
        ),
        delivery_id=delivery_id,
        outcome=OtpProviderReceiptOutcome.DELIVERED,
        occurred_at=occurred_at,
        received_at=now,
    )

    assert result.duplicate is False
    assert result.receipt.provider_event_ref == hashlib.sha256(
        event_id.encode("ascii")
    ).hexdigest()
    assert result.receipt.delivery_ref == hashlib.sha256(
        str(delivery_id).encode("ascii")
    ).hexdigest()
    serialized = repr(repository._receipts)
    assert event_id not in serialized
    assert str(delivery_id) not in serialized
    assert _SECRET.decode("ascii") not in serialized
    assert raw.decode("utf-8") not in serialized

    facts = service.facts(window=timedelta(hours=1), as_of=now)
    assert facts.total_count == 1
    assert facts.delivered_count == 1
    assert facts.undeliverable_count == 0
    assert facts.expired_count == 0


def test_exact_replay_is_idempotent_and_conflicting_reuse_is_rejected() -> None:
    service = _service()
    now = datetime(2026, 8, 6, 5, 10, tzinfo=UTC)
    delivery_id = uuid4()
    event_id = "evt_01J9K5R4X2Y7Z8A9B0C1D2E3FB"
    occurred_at = now - timedelta(seconds=5)
    timestamp = str(int(now.timestamp()))
    raw = _body(
        delivery_id=delivery_id,
        outcome="UNDELIVERABLE",
        occurred_at=occurred_at,
    )
    signature = _signature(
        raw_body=raw,
        timestamp=timestamp,
        event_id=event_id,
    )
    kwargs = {
        "raw_body": raw,
        "timestamp": timestamp,
        "key_id": _KEY_ID,
        "provider_event_id": event_id,
        "signature": signature,
        "delivery_id": delivery_id,
        "outcome": OtpProviderReceiptOutcome.UNDELIVERABLE,
        "occurred_at": occurred_at,
        "received_at": now,
    }

    assert service.receive(**kwargs).duplicate is False
    assert service.receive(**kwargs).duplicate is True

    conflicting_raw = _body(
        delivery_id=delivery_id,
        outcome="EXPIRED",
        occurred_at=occurred_at,
    )
    with pytest.raises(DomainError) as exc_info:
        service.receive(
            **{
                **kwargs,
                "raw_body": conflicting_raw,
                "signature": _signature(
                    raw_body=conflicting_raw,
                    timestamp=timestamp,
                    event_id=event_id,
                ),
                "outcome": OtpProviderReceiptOutcome.EXPIRED,
            }
        )
    assert exc_info.value.code == "AUTH_OTP_RECEIPT_EVENT_CONFLICT"
    assert exc_info.value.status_code == 409


def test_invalid_signature_stale_timestamp_and_unknown_key_are_indistinguishable() -> None:
    service = _service()
    now = datetime(2026, 8, 6, 5, 20, tzinfo=UTC)
    delivery_id = uuid4()
    event_id = "evt_01J9K5R4X2Y7Z8A9B0C1D2E3FC"
    occurred_at = now - timedelta(seconds=1)
    raw = _body(
        delivery_id=delivery_id,
        outcome="DELIVERED",
        occurred_at=occurred_at,
    )

    attempts = (
        {
            "timestamp": str(int(now.timestamp())),
            "key_id": _KEY_ID,
            "signature": "0" * 64,
        },
        {
            "timestamp": str(int((now - timedelta(minutes=6)).timestamp())),
            "key_id": _KEY_ID,
            "signature": "0" * 64,
        },
        {
            "timestamp": str(int(now.timestamp())),
            "key_id": "unknown-v1",
            "signature": "0" * 64,
        },
    )
    for attempt in attempts:
        with pytest.raises(DomainError) as exc_info:
            service.receive(
                raw_body=raw,
                timestamp=attempt["timestamp"],
                key_id=attempt["key_id"],
                provider_event_id=event_id,
                signature=attempt["signature"],
                delivery_id=delivery_id,
                outcome=OtpProviderReceiptOutcome.DELIVERED,
                occurred_at=occurred_at,
                received_at=now,
            )
        assert exc_info.value.code == "AUTH_OTP_RECEIPT_REJECTED"
        assert exc_info.value.status_code == 401


def test_disabled_receipt_boundary_is_fail_closed() -> None:
    service = OtpProviderReceiptService(
        repository=InMemoryOtpProviderReceiptRepository(),
        secret_resolver=None,
        enabled=False,
    )
    now = datetime(2026, 8, 6, 5, 30, tzinfo=UTC)
    with pytest.raises(DomainError) as exc_info:
        service.receive(
            raw_body=b"{}",
            timestamp=str(int(now.timestamp())),
            key_id=_KEY_ID,
            provider_event_id="evt_01J9K5R4X2Y7Z8A9B0C1D2E3FD",
            signature="0" * 64,
            delivery_id=uuid4(),
            outcome=OtpProviderReceiptOutcome.DELIVERED,
            occurred_at=now,
            received_at=now,
        )
    assert exc_info.value.code == "AUTH_OTP_RECEIPT_DISABLED"
    assert exc_info.value.status_code == 404
