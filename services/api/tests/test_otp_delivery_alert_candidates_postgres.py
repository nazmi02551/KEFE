from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

from kefe_api.infrastructure.postgres_otp_delivery_health import (
    PostgresOtpDeliveryHealthRepository,
)
from kefe_api.modules.identity.account_models import OtpChannel
from kefe_api.modules.identity.otp_delivery import OtpDeliveryOutcome
from kefe_api.modules.identity.otp_delivery_health import (
    OtpDeliveryAlertPolicy,
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
        connection.execute(
            text("DELETE FROM identity.otp_delivery_alert_acknowledgement")
        )
        connection.execute(text("DELETE FROM identity.otp_delivery_alert_candidate"))
        connection.execute(text("DELETE FROM identity.otp_delivery_event"))


def _health_policy() -> OtpDeliveryHealthPolicy:
    return OtpDeliveryHealthPolicy(
        window=timedelta(minutes=15),
        retention=timedelta(days=7),
        minimum_ratio_sample=100,
        failure_count_attention=1,
        failure_count_critical=2,
        unavailable_count_attention=1,
        unavailable_count_critical=2,
        failure_ratio_attention_bps=5_000,
        failure_ratio_critical_bps=8_000,
    )


def _alert_policy(
    *,
    cooldown: timedelta = timedelta(minutes=30),
    retention: timedelta = timedelta(days=30),
) -> OtpDeliveryAlertPolicy:
    return OtpDeliveryAlertPolicy(cooldown=cooldown, retention=retention)


def _repository(
    *,
    alert_policy: OtpDeliveryAlertPolicy | None = None,
) -> PostgresOtpDeliveryHealthRepository:
    return PostgresOtpDeliveryHealthRepository(
        _engine(),
        health_policy=_health_policy(),
        alert_policy=alert_policy or _alert_policy(),
    )


def _event(
    *,
    observed_at: datetime,
    outcome: OtpDeliveryOutcome = OtpDeliveryOutcome.UNAVAILABLE,
) -> OtpDeliveryHealthEvent:
    accepted = outcome is OtpDeliveryOutcome.ACCEPTED
    return OtpDeliveryHealthEvent(
        id=uuid4(),
        observed_at=observed_at,
        channel=OtpChannel.EMAIL,
        outcome=outcome,
        attempts=1,
        status_code=202 if accepted else 503,
        error_code=None if accepted else "OTP_PROVIDER_RETRYABLE_STATUS",
    )


def _append(
    repository: PostgresOtpDeliveryHealthRepository,
    *,
    observed_at: datetime,
    outcome: OtpDeliveryOutcome = OtpDeliveryOutcome.UNAVAILABLE,
) -> None:
    repository.append_and_prune(
        _event(observed_at=observed_at, outcome=outcome),
        prune_before=observed_at - _health_policy().retention,
    )


def test_postgres_alert_candidates_survive_restart_and_escalate() -> None:
    _clear()
    now = datetime.now(UTC)
    first_repository = _repository()
    first_service = OtpDeliveryHealthService(first_repository)

    _append(first_repository, observed_at=now)
    first = first_service.list_alert_candidates(as_of=now)
    assert len(first) == 1
    assert first[0].candidate.signal is OtpDeliveryHealthSignal.ATTENTION

    restarted_repository = _repository()
    restarted_service = OtpDeliveryHealthService(restarted_repository)
    restarted = restarted_service.list_alert_candidates(as_of=now + timedelta(seconds=1))
    assert restarted == first

    _append(restarted_repository, observed_at=now + timedelta(seconds=2))
    escalated = restarted_service.list_alert_candidates(
        as_of=now + timedelta(seconds=2)
    )
    assert [record.candidate.signal for record in escalated] == [
        OtpDeliveryHealthSignal.CRITICAL,
        OtpDeliveryHealthSignal.ATTENTION,
    ]


def test_postgres_concurrent_candidate_admission_is_deduplicated() -> None:
    _clear()
    now = datetime.now(UTC)

    def append(index: int) -> None:
        repository = _repository()
        _append(repository, observed_at=now + timedelta(microseconds=index))

    with ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(append, range(4)))

    records = OtpDeliveryHealthService(_repository()).list_alert_candidates(
        as_of=now + timedelta(seconds=1)
    )
    assert len(records) <= 2
    assert len({record.candidate.signal for record in records}) == len(records)
    assert records[0].candidate.signal is OtpDeliveryHealthSignal.CRITICAL


def test_postgres_acknowledgement_is_restart_durable_and_idempotent() -> None:
    _clear()
    now = datetime.now(UTC)
    repository = _repository()
    service = OtpDeliveryHealthService(repository)
    _append(repository, observed_at=now)
    candidate_id = service.list_alert_candidates(as_of=now)[0].candidate.id
    first_actor = f"admin:{uuid4()}"

    first = service.acknowledge_alert(
        candidate_id=candidate_id,
        actor_ref=first_actor,
        as_of=now + timedelta(minutes=1),
    )
    replay = OtpDeliveryHealthService(_repository()).acknowledge_alert(
        candidate_id=candidate_id,
        actor_ref=f"admin:{uuid4()}",
        as_of=now + timedelta(minutes=2),
    )
    assert first.acknowledgement is not None
    assert replay.acknowledgement == first.acknowledgement
    assert replay.acknowledgement.actor_ref == first_actor

    restarted = OtpDeliveryHealthService(_repository()).list_alert_candidates(
        acknowledged=True,
        as_of=now + timedelta(minutes=3),
    )
    assert restarted == (replay,)


def test_postgres_alert_retention_prunes_candidate_and_acknowledgement() -> None:
    _clear()
    now = datetime.now(UTC)
    policy = _alert_policy(
        cooldown=timedelta(minutes=1),
        retention=timedelta(hours=1),
    )
    repository = _repository(alert_policy=policy)
    service = OtpDeliveryHealthService(repository)
    _append(repository, observed_at=now)
    old = service.list_alert_candidates(as_of=now)[0]
    service.acknowledge_alert(
        candidate_id=old.candidate.id,
        actor_ref=f"admin:{uuid4()}",
        as_of=now + timedelta(minutes=1),
    )

    later = now + timedelta(hours=2)
    _append(repository, observed_at=later)
    records = service.list_alert_candidates(as_of=later)
    assert len(records) == 1
    assert records[0].candidate.id != old.candidate.id
    with _engine().connect() as connection:
        candidate_count = connection.execute(
            text("SELECT count(*) FROM identity.otp_delivery_alert_candidate")
        ).scalar_one()
        acknowledgement_count = connection.execute(
            text("SELECT count(*) FROM identity.otp_delivery_alert_acknowledgement")
        ).scalar_one()
    assert int(candidate_count) == 1
    assert int(acknowledgement_count) == 0


def test_postgres_alert_schema_is_aggregate_only_and_update_immutable() -> None:
    _clear()
    now = datetime.now(UTC)
    repository = _repository()
    service = OtpDeliveryHealthService(repository)
    _append(repository, observed_at=now)
    candidate_id = service.list_alert_candidates(as_of=now)[0].candidate.id
    service.acknowledge_alert(
        candidate_id=candidate_id,
        actor_ref=f"admin:{uuid4()}",
        as_of=now + timedelta(minutes=1),
    )

    with _engine().connect() as connection:
        candidate_columns = {
            row[0]
            for row in connection.execute(
                text(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'identity'
                      AND table_name = 'otp_delivery_alert_candidate'
                    """
                )
            ).all()
        }
        acknowledgement_columns = {
            row[0]
            for row in connection.execute(
                text(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'identity'
                      AND table_name = 'otp_delivery_alert_acknowledgement'
                    """
                )
            ).all()
        }
        foreign_keys = connection.execute(
            text(
                """
                SELECT
                    kcu.column_name,
                    ccu.table_schema,
                    ccu.table_name,
                    ccu.column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                 AND tc.constraint_schema = kcu.constraint_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON tc.constraint_name = ccu.constraint_name
                 AND tc.constraint_schema = ccu.constraint_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                  AND tc.table_schema = 'identity'
                  AND tc.table_name = 'otp_delivery_alert_acknowledgement'
                """
            )
        ).all()

    assert candidate_columns == {
        "id",
        "signal",
        "reason_codes",
        "observed_at",
        "window_started_at",
        "total_count",
        "accepted_count",
        "unavailable_count",
        "rejected_count",
        "failure_ratio_bps",
        "created_at",
    }
    assert acknowledgement_columns == {
        "candidate_id",
        "acknowledged_at",
        "actor_ref",
        "created_at",
    }
    assert foreign_keys == [
        (
            "candidate_id",
            "identity",
            "otp_delivery_alert_candidate",
            "id",
        )
    ]
    forbidden = {
        "recipient",
        "destination",
        "destination_hash",
        "otp_code",
        "otp_hash",
        "challenge_id",
        "delivery_id",
        "account_id",
        "user_id",
        "device_id",
        "session_id",
        "provider_request_body",
        "provider_response_body",
        "credential",
        "secret_ref",
        "endpoint",
        "provider_request_id",
    }
    assert not forbidden.intersection(candidate_columns | acknowledgement_columns)

    with pytest.raises(DBAPIError):
        with _engine().begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE identity.otp_delivery_alert_candidate
                    SET signal = signal
                    WHERE id = :candidate_id
                    """
                ),
                {"candidate_id": candidate_id},
            )
    with pytest.raises(DBAPIError):
        with _engine().begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE identity.otp_delivery_alert_acknowledgement
                    SET actor_ref = actor_ref
                    WHERE candidate_id = :candidate_id
                    """
                ),
                {"candidate_id": candidate_id},
            )
