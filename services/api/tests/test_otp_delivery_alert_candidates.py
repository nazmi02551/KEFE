from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from kefe_api.core.errors import DomainError
from kefe_api.modules.identity.account_models import OtpChannel
from kefe_api.modules.identity.otp_delivery import OtpDeliveryOutcome
from kefe_api.modules.identity.otp_delivery_health import (
    InMemoryOtpDeliveryHealthRepository,
    OtpDeliveryAlertPolicy,
    OtpDeliveryHealthEvent,
    OtpDeliveryHealthPolicy,
    OtpDeliveryHealthService,
    OtpDeliveryHealthSignal,
)


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


def _alert_policy() -> OtpDeliveryAlertPolicy:
    return OtpDeliveryAlertPolicy(
        cooldown=timedelta(minutes=5),
        retention=timedelta(days=30),
    )


def _repository() -> InMemoryOtpDeliveryHealthRepository:
    return InMemoryOtpDeliveryHealthRepository(
        health_policy=_health_policy(),
        alert_policy=_alert_policy(),
    )


def _event(
    *,
    observed_at: datetime,
    outcome: OtpDeliveryOutcome,
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
    repository: InMemoryOtpDeliveryHealthRepository,
    *,
    observed_at: datetime,
    outcome: OtpDeliveryOutcome,
) -> None:
    repository.append_and_prune(
        _event(observed_at=observed_at, outcome=outcome),
        prune_before=observed_at - _health_policy().retention,
    )


def test_alert_candidates_deduplicate_equal_severity_and_allow_escalation() -> None:
    now = datetime(2026, 8, 6, 0, 0, tzinfo=UTC)
    repository = _repository()
    service = OtpDeliveryHealthService(repository)

    _append(
        repository,
        observed_at=now,
        outcome=OtpDeliveryOutcome.UNAVAILABLE,
    )
    first = service.list_alert_candidates(as_of=now)
    assert len(first) == 1
    assert first[0].candidate.signal is OtpDeliveryHealthSignal.ATTENTION

    _append(
        repository,
        observed_at=now + timedelta(seconds=1),
        outcome=OtpDeliveryOutcome.UNAVAILABLE,
    )
    escalated = service.list_alert_candidates(as_of=now + timedelta(seconds=1))
    assert [item.candidate.signal for item in escalated] == [
        OtpDeliveryHealthSignal.CRITICAL,
        OtpDeliveryHealthSignal.ATTENTION,
    ]

    _append(
        repository,
        observed_at=now + timedelta(seconds=2),
        outcome=OtpDeliveryOutcome.UNAVAILABLE,
    )
    suppressed = service.list_alert_candidates(as_of=now + timedelta(seconds=2))
    assert len(suppressed) == 2

    _append(
        repository,
        observed_at=now + timedelta(minutes=6),
        outcome=OtpDeliveryOutcome.UNAVAILABLE,
    )
    after_cooldown = service.list_alert_candidates(
        as_of=now + timedelta(minutes=6)
    )
    assert len(after_cooldown) == 3
    assert after_cooldown[0].candidate.signal is OtpDeliveryHealthSignal.CRITICAL


def test_nominal_delivery_does_not_create_alert_candidate() -> None:
    now = datetime(2026, 8, 6, 0, 0, tzinfo=UTC)
    repository = _repository()
    _append(
        repository,
        observed_at=now,
        outcome=OtpDeliveryOutcome.ACCEPTED,
    )
    records = OtpDeliveryHealthService(repository).list_alert_candidates(as_of=now)
    assert records == ()


def test_acknowledgement_is_idempotent_and_never_means_resolution() -> None:
    now = datetime(2026, 8, 6, 0, 0, tzinfo=UTC)
    repository = _repository()
    service = OtpDeliveryHealthService(repository)
    _append(
        repository,
        observed_at=now,
        outcome=OtpDeliveryOutcome.UNAVAILABLE,
    )
    candidate_id = service.list_alert_candidates(as_of=now)[0].candidate.id

    first = service.acknowledge_alert(
        candidate_id=candidate_id,
        actor_ref=f"admin:{uuid4()}",
        as_of=now + timedelta(minutes=1),
    )
    replay = service.acknowledge_alert(
        candidate_id=candidate_id,
        actor_ref=f"admin:{uuid4()}",
        as_of=now + timedelta(minutes=2),
    )

    assert first.acknowledgement is not None
    assert replay.acknowledgement == first.acknowledgement
    assert replay.candidate.signal is OtpDeliveryHealthSignal.ATTENTION
    assert replay.acknowledged is True


def test_missing_alert_candidate_fails_closed() -> None:
    service = OtpDeliveryHealthService(_repository())
    with pytest.raises(DomainError) as captured:
        service.acknowledge_alert(
            candidate_id=uuid4(),
            actor_ref=f"admin:{uuid4()}",
            as_of=datetime(2026, 8, 6, 0, 0, tzinfo=UTC),
        )
    assert captured.value.code == "ADMIN_OPERATIONAL_ALERT_NOT_FOUND"
    assert captured.value.status_code == 404


def test_alert_candidate_records_are_aggregate_only_and_privacy_safe() -> None:
    now = datetime(2026, 8, 6, 0, 0, tzinfo=UTC)
    repository = _repository()
    service = OtpDeliveryHealthService(repository)
    _append(
        repository,
        observed_at=now,
        outcome=OtpDeliveryOutcome.UNAVAILABLE,
    )
    rendered = repr(service.list_alert_candidates(as_of=now)).lower()
    for forbidden in (
        "person@example.test",
        "+905551112233",
        "recipient",
        "destination_hash",
        "otp_code",
        "challenge_id",
        "delivery_id",
        "account_id",
        "user_id",
        "device_id",
        "provider_request_body",
        "provider_response_body",
        "credential",
        "secret_ref",
        "https://otp.example.test",
    ):
        assert forbidden not in rendered
