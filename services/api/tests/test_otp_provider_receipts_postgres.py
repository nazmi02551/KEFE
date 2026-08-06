from __future__ import annotations

import hashlib
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

from kefe_api.infrastructure.postgres_otp_provider_receipts import (
    PostgresOtpProviderReceiptRepository,
)
from kefe_api.modules.identity.otp_provider_receipts import (
    OtpProviderReceipt,
    OtpProviderReceiptConflict,
    OtpProviderReceiptOutcome,
)

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)


def _engine():
    return create_engine(os.environ["KEFE_DATABASE_URL"])


def _repository() -> PostgresOtpProviderReceiptRepository:
    return PostgresOtpProviderReceiptRepository(_engine())


def _clear() -> None:
    with _engine().begin() as connection:
        connection.execute(text("DELETE FROM identity.otp_provider_receipt"))


def _receipt(*, event_id: str, delivery_id, now: datetime) -> OtpProviderReceipt:
    return OtpProviderReceipt(
        provider_event_ref=hashlib.sha256(event_id.encode("ascii")).hexdigest(),
        delivery_ref=hashlib.sha256(
            str(delivery_id).encode("ascii")
        ).hexdigest(),
        outcome=OtpProviderReceiptOutcome.DELIVERED,
        occurred_at=now - timedelta(seconds=3),
        received_at=now,
    )


def test_postgres_receipt_survives_restart_and_exact_replay_is_idempotent() -> None:
    _clear()
    now = datetime.now(UTC)
    receipt = _receipt(
        event_id="evt_01J9K5R4X2Y7Z8A9B0C1D2E501",
        delivery_id=uuid4(),
        now=now,
    )
    first = _repository().append_and_prune(
        receipt,
        prune_before=now - timedelta(days=30),
    )
    restarted = _repository().append_and_prune(
        receipt,
        prune_before=now - timedelta(days=30),
    )

    assert first.duplicate is False
    assert restarted.duplicate is True
    facts = _repository().read_facts(
        window_started_at=now - timedelta(hours=1),
        as_of=now,
        prune_before=now - timedelta(days=30),
    )
    assert facts.total_count == 1
    assert facts.delivered_count == 1


def test_postgres_concurrent_duplicate_receipts_converge() -> None:
    _clear()
    now = datetime.now(UTC)
    receipt = _receipt(
        event_id="evt_01J9K5R4X2Y7Z8A9B0C1D2E502",
        delivery_id=uuid4(),
        now=now,
    )

    def append(_index: int):
        return _repository().append_and_prune(
            receipt,
            prune_before=now - timedelta(days=30),
        )

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = tuple(pool.map(append, range(4)))

    assert sum(not result.duplicate for result in results) == 1
    assert sum(result.duplicate for result in results) == 3


def test_postgres_conflicting_event_reuse_is_rejected() -> None:
    _clear()
    now = datetime.now(UTC)
    event_id = "evt_01J9K5R4X2Y7Z8A9B0C1D2E503"
    first = _receipt(event_id=event_id, delivery_id=uuid4(), now=now)
    second = OtpProviderReceipt(
        provider_event_ref=first.provider_event_ref,
        delivery_ref=hashlib.sha256(str(uuid4()).encode("ascii")).hexdigest(),
        outcome=OtpProviderReceiptOutcome.EXPIRED,
        occurred_at=first.occurred_at,
        received_at=now,
    )
    repository = _repository()
    repository.append_and_prune(first, prune_before=now - timedelta(days=30))

    with pytest.raises(OtpProviderReceiptConflict):
        repository.append_and_prune(
            second,
            prune_before=now - timedelta(days=30),
        )


def test_postgres_receipt_schema_is_privacy_safe_retained_and_immutable() -> None:
    _clear()
    now = datetime.now(UTC)
    old = _receipt(
        event_id="evt_01J9K5R4X2Y7Z8A9B0C1D2E504",
        delivery_id=uuid4(),
        now=now - timedelta(days=31),
    )
    current = _receipt(
        event_id="evt_01J9K5R4X2Y7Z8A9B0C1D2E505",
        delivery_id=uuid4(),
        now=now,
    )
    repository = _repository()
    repository.append_and_prune(old, prune_before=now - timedelta(days=60))
    repository.append_and_prune(current, prune_before=now - timedelta(days=30))

    with _engine().begin() as connection:
        columns = {
            row["column_name"]
            for row in connection.execute(
                text(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'identity'
                      AND table_name = 'otp_provider_receipt'
                    """
                )
            ).mappings()
        }
        assert columns == {
            "provider_event_ref",
            "delivery_ref",
            "outcome",
            "occurred_at",
            "received_at",
            "created_at",
        }
        assert connection.execute(
            text("SELECT count(*) FROM identity.otp_provider_receipt")
        ).scalar_one() == 1

    forbidden = {
        "recipient",
        "destination",
        "otp",
        "code",
        "payload",
        "signature",
        "secret",
        "endpoint",
        "delivery_id",
        "provider_event_id",
        "actor_id",
        "account_id",
        "device_id",
        "session_id",
    }
    assert columns.isdisjoint(forbidden)

    with pytest.raises(DBAPIError):
        with _engine().begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE identity.otp_provider_receipt
                    SET outcome = 'EXPIRED'
                    WHERE provider_event_ref = :event_ref
                    """
                ),
                {"event_ref": current.provider_event_ref},
            )
