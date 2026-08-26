from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from kefe_api.core.errors import DomainError
from kefe_api.core.settings import Settings, get_settings
from kefe_api.infrastructure.persistence import (
    build_account_continuity_repository,
    build_identity_repository,
)
from kefe_api.infrastructure.postgres_otp_request_guard import (
    GuardedPostgresAccountContinuityRepository,
)
from kefe_api.main import create_app
from kefe_api.modules.identity.account_in_memory import (
    InMemoryAccountContinuityRepository,
)
from kefe_api.modules.identity.account_models import OtpChallenge, OtpChannel
from kefe_api.modules.identity.account_service import AccountContinuityService
from kefe_api.modules.identity.in_memory import InMemoryIdentityRepository
from kefe_api.modules.identity.otp_delivery import CapturingOtpDelivery
from kefe_api.modules.identity.otp_request_guard import (
    GuardedInMemoryAccountContinuityRepository,
    OtpRequestAbusePolicy,
)

_PRODUCTION_DATABASE_URL = "postgresql+psycopg://kefe:secret@db.internal:5432/kefe"
_PRODUCTION_REPLAY_SECRET = "production-account-merge-replay-secret-0001"


def _production_settings(**overrides: object) -> Settings:
    values = {
        "environment": "production",
        "persistence_backend": "postgres",
        "database_url": _PRODUCTION_DATABASE_URL,
        "account_merge_replay_secret": _PRODUCTION_REPLAY_SECRET,
        "otp_delivery_mode": "DISABLED",
        **overrides,
    }
    return Settings(**values)


class FailingDelivery:
    def send(self, **kwargs) -> None:
        del kwargs
        raise DomainError(
            "AUTH_OTP_DELIVERY_UNAVAILABLE",
            "OTP delivery provider is temporarily unavailable",
            503,
            retryable=True,
        )


def _guarded_service(
    *,
    delivery=None,
    cooldown_seconds: int = 60,
    window_seconds: int = 900,
    window_limit: int = 5,
) -> tuple[AccountContinuityService, object]:
    settings = Settings(
        otp_request_guard_mode="ENFORCE",
        otp_request_cooldown_seconds=cooldown_seconds,
        otp_request_window_seconds=window_seconds,
        otp_request_window_limit=window_limit,
        otp_request_guard_retention_seconds=max(window_seconds, 3_600),
    )
    identity = InMemoryIdentityRepository()
    repository = build_account_continuity_repository(settings, identity)
    return (
        AccountContinuityService(
            repository=repository,
            delivery=delivery or CapturingOtpDelivery(),
        ),
        repository,
    )


def _challenge(
    requested_at: datetime,
    *,
    channel: OtpChannel = OtpChannel.EMAIL,
    identifier_hash: str = "a" * 64,
) -> OtpChallenge:
    return OtpChallenge(
        id=uuid4(),
        channel=channel,
        identifier_hash=identifier_hash,
        identifier_hint="te***@example.test",
        code_hash="b" * 64,
        requested_at=requested_at,
        expires_at=requested_at + timedelta(minutes=10),
    )


def test_auto_mode_is_compatible_in_development_and_enforced_in_production() -> None:
    development_identity = InMemoryIdentityRepository()
    development = build_account_continuity_repository(
        Settings(environment="development", otp_request_guard_mode="AUTO"),
        development_identity,
    )
    assert isinstance(development, InMemoryAccountContinuityRepository)
    assert not isinstance(development, GuardedInMemoryAccountContinuityRepository)

    production_settings = _production_settings(otp_request_guard_mode="AUTO")
    production_identity = build_identity_repository(production_settings)
    production = build_account_continuity_repository(
        production_settings,
        production_identity,
    )
    assert isinstance(production, GuardedPostgresAccountContinuityRepository)


def test_production_cannot_disable_otp_request_guard() -> None:
    with pytest.raises(
        ValidationError,
        match="KEFE_OTP_REQUEST_GUARD_MODE=OFF",
    ):
        _production_settings(otp_request_guard_mode="OFF")


def test_normalized_destination_is_limited_before_second_delivery() -> None:
    delivery = CapturingOtpDelivery()
    service, _ = _guarded_service(delivery=delivery)

    first = service.request_otp(
        channel=OtpChannel.EMAIL,
        identifier=" Person@Example.Test ",
    )
    with pytest.raises(DomainError) as captured:
        service.request_otp(
            channel=OtpChannel.EMAIL,
            identifier="person@example.test",
        )

    assert first.identifier_hint == "pe***@example.test"
    assert captured.value.code == "AUTH_RATE_LIMITED"
    assert captured.value.status_code == 429
    assert captured.value.retryable is True
    assert len(delivery.deliveries) == 1


def test_delivery_failure_still_consumes_destination_quota() -> None:
    service, repository = _guarded_service(delivery=FailingDelivery())

    with pytest.raises(DomainError) as first:
        service.request_otp(
            channel=OtpChannel.EMAIL,
            identifier="provider-failure@example.test",
        )
    with pytest.raises(DomainError) as second:
        service.request_otp(
            channel=OtpChannel.EMAIL,
            identifier="provider-failure@example.test",
        )

    assert first.value.code == "AUTH_OTP_DELIVERY_UNAVAILABLE"
    assert second.value.code == "AUTH_RATE_LIMITED"
    assert isinstance(repository, GuardedInMemoryAccountContinuityRepository)


def test_memory_guard_enforces_window_reset_and_channel_isolation() -> None:
    policy = OtpRequestAbusePolicy.from_seconds(
        cooldown_seconds=10,
        window_seconds=60,
        window_limit=2,
        retention_seconds=120,
    )
    repository = GuardedInMemoryAccountContinuityRepository(
        InMemoryIdentityRepository(),
        policy,
    )
    started_at = datetime(2026, 8, 5, 17, 0, tzinfo=UTC)

    repository.create_challenge(_challenge(started_at))
    repository.create_challenge(_challenge(started_at + timedelta(seconds=10)))
    with pytest.raises(DomainError, match="OTP request rate limit exceeded"):
        repository.create_challenge(_challenge(started_at + timedelta(seconds=20)))

    repository.create_challenge(
        _challenge(
            started_at + timedelta(seconds=20),
            channel=OtpChannel.SMS,
        )
    )
    repository.create_challenge(_challenge(started_at + timedelta(seconds=60)))


def test_concurrent_memory_requests_admit_exactly_one_delivery() -> None:
    delivery = CapturingOtpDelivery()
    service, _ = _guarded_service(delivery=delivery, cooldown_seconds=300)

    def submit() -> str:
        try:
            service.request_otp(
                channel=OtpChannel.EMAIL,
                identifier="memory-race@example.test",
            )
        except DomainError as exc:
            return exc.code
        return "CREATED"

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = sorted(executor.map(lambda _: submit(), range(2)))

    assert results == ["AUTH_RATE_LIMITED", "CREATED"]
    assert len(delivery.deliveries) == 1


def test_http_surface_returns_registered_retryable_problem(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("KEFE_OTP_REQUEST_GUARD_MODE", "ENFORCE")
    monkeypatch.setenv("KEFE_OTP_REQUEST_COOLDOWN_SECONDS", "300")
    get_settings.cache_clear()
    try:
        app = create_app()
        client = TestClient(app)
        payload = {
            "channel": "EMAIL",
            "identifier": "surface-limit@example.test",
        }
        first = client.post("/v1/auth/otp/request", json=payload)
        second = client.post("/v1/auth/otp/request", json=payload)

        assert first.status_code == 201
        assert second.status_code == 429
        assert second.headers["content-type"].startswith("application/problem+json")
        assert second.json()["code"] == "AUTH_RATE_LIMITED"
        assert second.json()["retryable"] is True
        assert "surface-limit@example.test" not in second.text
    finally:
        get_settings.cache_clear()
