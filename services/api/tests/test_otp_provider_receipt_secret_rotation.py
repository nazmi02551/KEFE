from __future__ import annotations

import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from kefe_api.modules.identity.otp_provider_receipts import (
    InMemoryOtpProviderReceiptRepository,
    OtpProviderReceiptOutcome,
    OtpProviderReceiptService,
    RegistryBackedOtpProviderReceiptSecretLeaseResolver,
)
from kefe_api.modules.identity.otp_secret_resolution import (
    EnvironmentSecretReferenceResolver,
)
from kefe_api.modules.knowledge.provider_secret_execution import (
    InMemorySecretResolverRegistry,
)

_OLD_KEY = "receipt-old-v1"
_NEW_KEY = "receipt-new-v2"
_OLD_REF = "envref://KEFE_RECEIPT_OLD"
_NEW_REF = "envref://KEFE_RECEIPT_NEW"
_OLD_SECRET = "old-receipt-secret-material-01234567890123456789"
_NEW_SECRET = "new-receipt-secret-material-01234567890123456789"
_ROTATED_SECRET = "rotated-receipt-secret-material-012345678901234"


def _raw(*, delivery_id, occurred_at: datetime) -> bytes:
    return json.dumps(
        {
            "delivery_id": str(delivery_id),
            "occurred_at": occurred_at.isoformat(),
            "outcome": "DELIVERED",
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _signature(
    *,
    secret: str,
    key_id: str,
    event_id: str,
    timestamp: str,
    raw_body: bytes,
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
    return hmac.new(
        secret.encode("ascii"),
        canonical,
        hashlib.sha256,
    ).hexdigest()


def test_overlapping_key_ids_and_live_secret_rotation_require_no_process_restart() -> None:
    values = {
        "KEFE_RECEIPT_OLD": _OLD_SECRET,
        "KEFE_RECEIPT_NEW": _NEW_SECRET,
    }
    registry = InMemorySecretResolverRegistry(
        (EnvironmentSecretReferenceResolver(values.get),)
    )
    resolver = RegistryBackedOtpProviderReceiptSecretLeaseResolver(
        registry=registry,
        secret_refs={_OLD_KEY: _OLD_REF, _NEW_KEY: _NEW_REF},
        lease_ttl_seconds=30,
    )
    service = OtpProviderReceiptService(
        repository=InMemoryOtpProviderReceiptRepository(),
        secret_resolver=resolver,
        enabled=True,
    )
    now = datetime(2026, 8, 6, 6, 0, tzinfo=UTC)

    attempts = [
        (_OLD_KEY, _OLD_SECRET, "evt_01J9K5R4X2Y7Z8A9B0C1D2E601"),
        (_NEW_KEY, _NEW_SECRET, "evt_01J9K5R4X2Y7Z8A9B0C1D2E602"),
    ]
    for key_id, secret, event_id in attempts:
        delivery_id = uuid4()
        occurred_at = now - timedelta(seconds=5)
        raw_body = _raw(delivery_id=delivery_id, occurred_at=occurred_at)
        timestamp = str(int(now.timestamp()))
        result = service.receive(
            raw_body=raw_body,
            timestamp=timestamp,
            key_id=key_id,
            provider_event_id=event_id,
            signature=_signature(
                secret=secret,
                key_id=key_id,
                event_id=event_id,
                timestamp=timestamp,
                raw_body=raw_body,
            ),
            delivery_id=delivery_id,
            outcome=OtpProviderReceiptOutcome.DELIVERED,
            occurred_at=occurred_at,
            received_at=now,
        )
        assert result.duplicate is False

    values["KEFE_RECEIPT_NEW"] = _ROTATED_SECRET
    delivery_id = uuid4()
    occurred_at = now - timedelta(seconds=4)
    raw_body = _raw(delivery_id=delivery_id, occurred_at=occurred_at)
    timestamp = str(int(now.timestamp()))
    rotated = service.receive(
        raw_body=raw_body,
        timestamp=timestamp,
        key_id=_NEW_KEY,
        provider_event_id="evt_01J9K5R4X2Y7Z8A9B0C1D2E603",
        signature=_signature(
            secret=_ROTATED_SECRET,
            key_id=_NEW_KEY,
            event_id="evt_01J9K5R4X2Y7Z8A9B0C1D2E603",
            timestamp=timestamp,
            raw_body=raw_body,
        ),
        delivery_id=delivery_id,
        outcome=OtpProviderReceiptOutcome.DELIVERED,
        occurred_at=occurred_at,
        received_at=now,
    )

    assert rotated.duplicate is False
    assert service.facts(window=timedelta(hours=1), as_of=now).total_count == 3
    rendered = f"{resolver!r} {service!r}"
    for forbidden in (
        _OLD_REF,
        _NEW_REF,
        _OLD_SECRET,
        _NEW_SECRET,
        _ROTATED_SECRET,
    ):
        assert forbidden not in rendered
