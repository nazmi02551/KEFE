from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text

from kefe_api.core.settings import get_settings
from kefe_api.infrastructure.postgres_otp_delivery_health import (
    PostgresOtpDeliveryHealthRepository,
)
from kefe_api.main import create_app
from kefe_api.modules.identity.account_models import OtpChannel
from kefe_api.modules.identity.otp_delivery import (
    OtpDeliveryOperationalResult,
    OtpDeliveryOutcome,
)
from kefe_api.modules.identity.otp_delivery_health import (
    OtpDeliveryHealthEvent,
    OtpDeliveryHealthPolicy,
    OtpDeliveryHealthService,
    OtpDeliveryHealthSignal,
)

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)


def _engine():
    return create_engine(os.environ["KEFE_DATABASE_URL"])


def _clear() -> None:
    with _engine().begin() as connection:
        connection.execute(text("DELETE FROM identity.otp_delivery_event"))


def _app(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("KEFE_PERSISTENCE_BACKEND", "postgres")
    get_settings.cache_clear()
    return create_app()


def _event(
    *,
    observed_at: datetime,
    outcome: OtpDeliveryOutcome,
    channel: OtpChannel = OtpChannel.EMAIL,
) -> OtpDeliveryHealthEvent:
    accepted = outcome is OtpDeliveryOutcome.ACCEPTED
    return OtpDeliveryHealthEvent(
        id=uuid4(),
        observed_at=observed_at,
        channel=channel,
        outcome=outcome,
        attempts=1,
        status_code=202 if accepted else 503,
        error_code=None if accepted else "OTP_PROVIDER_RETRYABLE_STATUS",
    )


def test_postgres_delivery_health_survives_application_restart(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear()
    first_app = _app(monkeypatch)
    first_app.state.otp_delivery_health_observer.record(
        OtpDeliveryOperationalResult(
            outcome=OtpDeliveryOutcome.ACCEPTED,
            channel=OtpChannel.EMAIL,
            attempts=1,
            status_code=202,
            error_code=None,
        )
    )
    first_app.state.otp_delivery_health_observer.record(
        OtpDeliveryOperationalResult(
            outcome=OtpDeliveryOutcome.UNAVAILABLE,
            channel=OtpChannel.SMS,
            attempts=2,
            status_code=503,
            error_code="OTP_PROVIDER_RETRYABLE_STATUS",
        )
    )
    first = first_app.state.otp_delivery_health_service.snapshot(
        first_app.state.otp_delivery_health_policy
    )
    assert first.facts.total_count == 2
    assert first.facts.accepted_count == 1
    assert first.facts.unavailable_count == 1
    assert first.facts.email_count == 1
    assert first.facts.sms_count == 1

    get_settings.cache_clear()
    restarted_app = create_app()
    restarted = restarted_app.state.otp_delivery_health_service.snapshot(
        restarted_app.state.otp_delivery_health_policy
    )
    assert restarted.facts.total_count == first.facts.total_count
    assert restarted.facts.accepted_count == first.facts.accepted_count
    assert restarted.facts.unavailable_count == first.facts.unavailable_count
    assert restarted.facts.attempts_total == first.facts.attempts_total
    get_settings.cache_clear()


def test_postgres_snapshot_prunes_events_outside_retention(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear()
    _app(monkeypatch)
    now = datetime.now(UTC)
    repository = PostgresOtpDeliveryHealthRepository(_engine())
    repository.append_and_prune(
        _event(
            observed_at=now - timedelta(days=8),
            outcome=OtpDeliveryOutcome.UNAVAILABLE,
        ),
        prune_before=now - timedelta(days=30),
    )
    repository.append_and_prune(
        _event(observed_at=now, outcome=OtpDeliveryOutcome.ACCEPTED),
        prune_before=now - timedelta(days=30),
    )

    snapshot = OtpDeliveryHealthService(repository).snapshot(
        OtpDeliveryHealthPolicy(retention=timedelta(days=7)),
        as_of=now,
    )
    assert snapshot.facts.total_count == 1
    assert snapshot.facts.accepted_count == 1
    with _engine().connect() as connection:
        persisted = connection.execute(
            text("SELECT count(*) FROM identity.otp_delivery_event")
        ).scalar_one()
    assert int(persisted) == 1
    get_settings.cache_clear()


def test_postgres_aggregate_thresholds_are_deterministic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear()
    _app(monkeypatch)
    now = datetime.now(UTC)
    repository = PostgresOtpDeliveryHealthRepository(_engine())
    for index, outcome in enumerate(
        (
            OtpDeliveryOutcome.ACCEPTED,
            OtpDeliveryOutcome.UNAVAILABLE,
            OtpDeliveryOutcome.REJECTED,
            OtpDeliveryOutcome.UNAVAILABLE,
        )
    ):
        repository.append_and_prune(
            _event(
                observed_at=now - timedelta(seconds=index),
                outcome=outcome,
                channel=(OtpChannel.EMAIL if index % 2 == 0 else OtpChannel.SMS),
            ),
            prune_before=now - timedelta(days=7),
        )
    snapshot = OtpDeliveryHealthService(repository).snapshot(
        OtpDeliveryHealthPolicy(
            minimum_ratio_sample=4,
            failure_count_attention=2,
            failure_count_critical=3,
            unavailable_count_attention=2,
            unavailable_count_critical=4,
            failure_ratio_attention_bps=5_000,
            failure_ratio_critical_bps=7_500,
        ),
        as_of=now,
    )
    assert snapshot.signal is OtpDeliveryHealthSignal.CRITICAL
    assert snapshot.failure_ratio_bps == 7_500
    assert "FAILURE_COUNT_CRITICAL" in snapshot.reason_codes
    assert "FAILURE_RATIO_CRITICAL" in snapshot.reason_codes
    assert snapshot.facts.email_count == 2
    assert snapshot.facts.sms_count == 2
    get_settings.cache_clear()


def test_postgres_health_schema_is_privacy_safe_and_append_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _app(monkeypatch)
    with _engine().connect() as connection:
        columns = {
            row[0]
            for row in connection.execute(
                text(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'identity'
                      AND table_name = 'otp_delivery_event'
                    """
                )
            ).all()
        }
        foreign_keys = connection.execute(
            text(
                """
                SELECT count(*)
                FROM information_schema.table_constraints
                WHERE table_schema = 'identity'
                  AND table_name = 'otp_delivery_event'
                  AND constraint_type = 'FOREIGN KEY'
                """
            )
        ).scalar_one()
    assert columns == {
        "id",
        "observed_at",
        "channel",
        "outcome",
        "attempts",
        "status_code",
        "error_code",
        "created_at",
    }
    assert int(foreign_keys) == 0
    assert not {
        "identifier",
        "identifier_hash",
        "identifier_hint",
        "recipient",
        "otp_code",
        "code_hash",
        "challenge_id",
        "delivery_id",
        "request_body",
        "response_body",
        "bearer_token",
        "endpoint",
    } & columns
    get_settings.cache_clear()
