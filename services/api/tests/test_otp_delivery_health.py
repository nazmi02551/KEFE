from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from kefe_api.core.errors import DomainError
from kefe_api.core.settings import get_settings
from kefe_api.main import create_app
from kefe_api.modules.admin_security.in_memory import InMemoryAdminSessionStore
from kefe_api.modules.admin_security.models import AdminRole
from kefe_api.modules.admin_security.router import ADMIN_SESSION_COOKIE
from kefe_api.modules.identity.account_models import OtpChannel
from kefe_api.modules.identity.otp_delivery import (
    HttpOtpDelivery,
    OtpDeliveryOperationalResult,
    OtpDeliveryOutcome,
    OtpHttpResponse,
)
from kefe_api.modules.identity.otp_delivery_health import (
    DurableOtpDeliveryObserver,
    FailOpenOtpDeliveryObserver,
    InMemoryOtpDeliveryHealthRepository,
    OtpDeliveryHealthEvent,
    OtpDeliveryHealthPolicy,
    OtpDeliveryHealthService,
    OtpDeliveryHealthSignal,
)

ENDPOINT = "/internal/admin/v1/operational-reports/snapshot"


class StaticTransport:
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code
        self.calls = 0

    def execute(self, request) -> OtpHttpResponse:
        del request
        self.calls += 1
        return OtpHttpResponse(status_code=self.status_code, response_bytes=0)


class ExplodingObserver:
    def record(self, result: OtpDeliveryOperationalResult) -> None:
        del result
        raise RuntimeError("telemetry store unavailable")


def _event(
    *,
    observed_at: datetime,
    outcome: OtpDeliveryOutcome,
    channel: OtpChannel = OtpChannel.EMAIL,
    attempts: int = 1,
) -> OtpDeliveryHealthEvent:
    accepted = outcome is OtpDeliveryOutcome.ACCEPTED
    return OtpDeliveryHealthEvent(
        id=uuid4(),
        observed_at=observed_at,
        channel=channel,
        outcome=outcome,
        attempts=attempts,
        status_code=202 if accepted else 503,
        error_code=None if accepted else "OTP_PROVIDER_RETRYABLE_STATUS",
    )


def _issue_reviewer(app) -> TestClient:
    store = app.state.admin_session_store
    assert isinstance(store, InMemoryAdminSessionStore)
    subject_id = uuid4()
    store.upsert_subject(subject_id, roles=frozenset({AdminRole.REVIEWER}))
    now = datetime.now(UTC)
    issued = store.issue(
        admin_subject_id=subject_id,
        authenticated_at=now,
        mfa_satisfied_at=now,
        expires_at=now + timedelta(hours=1),
    )
    client = TestClient(app)
    client.cookies.set(ADMIN_SESSION_COOKIE, issued.session_token)
    return client


def test_health_snapshot_distinguishes_quiet_nominal_attention_and_critical() -> None:
    now = datetime(2026, 8, 5, 18, 0, tzinfo=UTC)
    repository = InMemoryOtpDeliveryHealthRepository()
    service = OtpDeliveryHealthService(repository)
    policy = OtpDeliveryHealthPolicy(
        minimum_ratio_sample=4,
        failure_count_attention=2,
        failure_count_critical=4,
        unavailable_count_attention=2,
        unavailable_count_critical=4,
        failure_ratio_attention_bps=5_000,
        failure_ratio_critical_bps=7_500,
    )

    assert service.snapshot(policy, as_of=now).signal is OtpDeliveryHealthSignal.QUIET

    repository.append_and_prune(
        _event(observed_at=now - timedelta(minutes=4), outcome=OtpDeliveryOutcome.ACCEPTED),
        prune_before=now - policy.retention,
    )
    assert service.snapshot(policy, as_of=now).signal is OtpDeliveryHealthSignal.NOMINAL

    for seconds in (3, 2):
        repository.append_and_prune(
            _event(
                observed_at=now - timedelta(minutes=seconds),
                outcome=OtpDeliveryOutcome.UNAVAILABLE,
            ),
            prune_before=now - policy.retention,
        )
    attention = service.snapshot(policy, as_of=now)
    assert attention.signal is OtpDeliveryHealthSignal.ATTENTION
    assert "FAILURE_COUNT_ATTENTION" in attention.reason_codes
    assert "UNAVAILABLE_COUNT_ATTENTION" in attention.reason_codes

    for seconds in (90, 30):
        repository.append_and_prune(
            _event(
                observed_at=now - timedelta(seconds=seconds),
                outcome=OtpDeliveryOutcome.UNAVAILABLE,
            ),
            prune_before=now - policy.retention,
        )
    critical = service.snapshot(policy, as_of=now)
    assert critical.signal is OtpDeliveryHealthSignal.CRITICAL
    assert "FAILURE_COUNT_CRITICAL" in critical.reason_codes
    assert "UNAVAILABLE_COUNT_CRITICAL" in critical.reason_codes


def test_failure_ratio_is_suppressed_below_minimum_sample() -> None:
    now = datetime(2026, 8, 5, 18, 0, tzinfo=UTC)
    repository = InMemoryOtpDeliveryHealthRepository()
    repository.append_and_prune(
        _event(observed_at=now, outcome=OtpDeliveryOutcome.REJECTED),
        prune_before=now - timedelta(days=7),
    )
    snapshot = OtpDeliveryHealthService(repository).snapshot(
        OtpDeliveryHealthPolicy(
            minimum_ratio_sample=5,
            failure_count_attention=10,
            failure_count_critical=20,
            unavailable_count_attention=10,
            unavailable_count_critical=20,
        ),
        as_of=now,
    )
    assert snapshot.failure_ratio_bps is None
    assert snapshot.signal is OtpDeliveryHealthSignal.NOMINAL
    assert not any("RATIO" in code for code in snapshot.reason_codes)


def test_snapshot_prunes_events_outside_retention() -> None:
    now = datetime(2026, 8, 5, 18, 0, tzinfo=UTC)
    repository = InMemoryOtpDeliveryHealthRepository()
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


def test_fail_open_observer_never_masks_provider_success_or_error() -> None:
    observer = FailOpenOtpDeliveryObserver(ExplodingObserver())
    accepted_transport = StaticTransport(202)
    accepted = HttpOtpDelivery(
        endpoint="https://otp.example.test/v1/send",
        bearer_token="managed-provider-secret-01234567890123456789",
        timeout_ms=1_000,
        max_response_bytes=1_024,
        max_attempts=1,
        transport=accepted_transport,
        observer=observer,
    )
    accepted.send(
        delivery_id=uuid4(),
        channel=OtpChannel.EMAIL,
        identifier="person@example.test",
        code="123456",
        expires_at=datetime.now(UTC) + timedelta(minutes=10),
    )
    assert accepted_transport.calls == 1

    unavailable_transport = StaticTransport(503)
    unavailable = HttpOtpDelivery(
        endpoint="https://otp.example.test/v1/send",
        bearer_token="managed-provider-secret-01234567890123456789",
        timeout_ms=1_000,
        max_response_bytes=1_024,
        max_attempts=1,
        transport=unavailable_transport,
        observer=observer,
    )
    with pytest.raises(DomainError) as captured:
        unavailable.send(
            delivery_id=uuid4(),
            channel=OtpChannel.SMS,
            identifier="+905551112233",
            code="654321",
            expires_at=datetime.now(UTC) + timedelta(minutes=10),
        )
    assert captured.value.code == "AUTH_OTP_DELIVERY_UNAVAILABLE"
    assert unavailable_transport.calls == 1


def test_durable_observer_records_only_operational_result() -> None:
    now = datetime(2026, 8, 5, 18, 0, tzinfo=UTC)
    repository = InMemoryOtpDeliveryHealthRepository()
    observer = DurableOtpDeliveryObserver(
        repository,
        retention=timedelta(days=7),
        clock=lambda: now,
    )
    observer.record(
        OtpDeliveryOperationalResult(
            outcome=OtpDeliveryOutcome.ACCEPTED,
            channel=OtpChannel.EMAIL,
            attempts=1,
            status_code=202,
            error_code=None,
        )
    )
    snapshot = OtpDeliveryHealthService(repository).snapshot(as_of=now)
    assert snapshot.facts.total_count == 1
    assert snapshot.facts.email_count == 1
    rendered = repr(repository._events)
    for forbidden in (
        "person@example.test",
        "123456",
        "authorization",
        "bearer",
        "https://otp.example.test",
    ):
        assert forbidden not in rendered.lower()


def test_secured_admin_report_surfaces_only_aggregate_critical_reason(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("KEFE_OTP_DELIVERY_HEALTH_FAILURE_ATTENTION", "1")
    monkeypatch.setenv("KEFE_OTP_DELIVERY_HEALTH_FAILURE_CRITICAL", "1")
    monkeypatch.setenv("KEFE_OTP_DELIVERY_HEALTH_UNAVAILABLE_ATTENTION", "1")
    monkeypatch.setenv("KEFE_OTP_DELIVERY_HEALTH_UNAVAILABLE_CRITICAL", "1")
    monkeypatch.setenv("KEFE_OTP_DELIVERY_HEALTH_MINIMUM_RATIO_SAMPLE", "100")
    get_settings.cache_clear()
    try:
        app = create_app()
        app.state.otp_delivery_health_observer.record(
            OtpDeliveryOperationalResult(
                outcome=OtpDeliveryOutcome.UNAVAILABLE,
                channel=OtpChannel.SMS,
                attempts=2,
                status_code=503,
                error_code="OTP_PROVIDER_RETRYABLE_STATUS",
            )
        )
        response = _issue_reviewer(app).get(ENDPOINT)
        assert response.status_code == 200
        body = response.json()
        assert body["overall_signal"] == "CRITICAL"
        assert "OTP_DELIVERY_CRITICAL" in body["reason_codes"]
        assert "otp_delivery" not in body
        rendered = str(body).lower()
        for forbidden in (
            "recipient",
            "identifier",
            "otp_code",
            "delivery_id",
            "bearer",
            "provider endpoint",
        ):
            assert forbidden not in rendered
    finally:
        get_settings.cache_clear()
