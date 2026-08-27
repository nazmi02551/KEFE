from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import SecretStr

from kefe_api.core.errors import DomainError
from kefe_api.core.settings import Settings
from kefe_api.modules.identity.account_models import OtpChannel
from kefe_api.modules.identity.otp_delivery import (
    HttpOtpDelivery,
    InMemoryOtpDeliveryObserver,
    OtpDeliveryOutcome,
    OtpHttpRequest,
    OtpHttpResponse,
    build_otp_delivery,
)
from kefe_api.modules.identity.otp_secret_resolution import (
    EnvironmentSecretReferenceResolver,
    RegistryBackedOtpSecretLeaseResolver,
    build_otp_secret_lease_resolver,
)
from kefe_api.modules.knowledge.provider_secret_execution import (
    InMemorySecretResolverRegistry,
    SecretLease,
    SecretResolutionFinalError,
    SecretResolutionRetryableError,
)

_ENDPOINT = "https://otp.provider.example/v1/deliveries"
_TOKEN_A = "rotation-token-a-012345678901234567890123456789"
_TOKEN_B = "rotation-token-b-012345678901234567890123456789"
_SECRET_REF = "envref://KEFE_OTP_PROVIDER_CREDENTIAL"
_PRODUCTION_DATABASE_URL = "postgresql+psycopg://kefe:secret@db.internal:5432/kefe"
_PRODUCTION_REPLAY_SECRET = "production-account-merge-replay-secret-0001"
_PRODUCTION_SESSION_SECRET = "production-session-renewal-secret-0000000001"


def _production_settings(**overrides: object) -> Settings:
    values = {
        "environment": "production",
        "persistence_backend": "postgres",
        "database_url": _PRODUCTION_DATABASE_URL,
        "account_merge_replay_secret": _PRODUCTION_REPLAY_SECRET,
        "session_renewal_secret": _PRODUCTION_SESSION_SECRET,
        "otp_delivery_mode": "DISABLED",
        **overrides,
    }
    return Settings(**values)


class SequenceTransport:
    def __init__(self, outcomes: list[OtpHttpResponse]) -> None:
        self.outcomes = list(outcomes)
        self.requests: list[OtpHttpRequest] = []

    def execute(self, request: OtpHttpRequest) -> OtpHttpResponse:
        self.requests.append(request)
        return self.outcomes.pop(0)


class RotatingOtpResolver:
    def __init__(self, materials: list[str]) -> None:
        self.materials = list(materials)
        self.leases: list[SecretLease] = []
        self.calls = 0

    def resolve(self, *, at: datetime, expires_at: datetime) -> SecretLease:
        self.calls += 1
        lease = SecretLease(
            self.materials.pop(0).encode("ascii"),
            expires_at=min(expires_at, at + timedelta(seconds=30)),
        )
        self.leases.append(lease)
        return lease

    def __repr__(self) -> str:
        return "RotatingOtpResolver(material=<redacted>)"


class FailingOtpResolver:
    def __init__(self, error: Exception) -> None:
        self.error = error
        self.calls = 0

    def resolve(self, *, at: datetime, expires_at: datetime) -> SecretLease:
        del at, expires_at
        self.calls += 1
        raise self.error


def _delivery(
    *,
    resolver,
    transport: SequenceTransport,
    observer: InMemoryOtpDeliveryObserver | None = None,
    max_attempts: int = 2,
) -> HttpOtpDelivery:
    return HttpOtpDelivery(
        endpoint=_ENDPOINT,
        secret_resolver=resolver,
        timeout_ms=1_000,
        max_response_bytes=1_024,
        max_attempts=max_attempts,
        transport=transport,
        observer=observer,
    )


def _send(delivery: HttpOtpDelivery, *, identifier: str = "person@example.test") -> None:
    delivery.send(
        delivery_id=uuid4(),
        channel=OtpChannel.EMAIL,
        identifier=identifier,
        code="123456",
        expires_at=datetime.now(UTC) + timedelta(minutes=10),
    )


def test_each_logical_send_resolves_current_secret_and_closes_lease() -> None:
    resolver = RotatingOtpResolver([_TOKEN_A, _TOKEN_B])
    transport = SequenceTransport(
        [
            OtpHttpResponse(status_code=202, response_bytes=0),
            OtpHttpResponse(status_code=202, response_bytes=0),
        ]
    )
    delivery = _delivery(resolver=resolver, transport=transport)

    _send(delivery, identifier="first@example.test")
    _send(delivery, identifier="second@example.test")

    assert resolver.calls == 2
    assert dict(transport.requests[0].headers)["authorization"] == f"Bearer {_TOKEN_A}"
    assert dict(transport.requests[1].headers)["authorization"] == f"Bearer {_TOKEN_B}"
    assert all(lease.closed for lease in resolver.leases)
    rendered = repr(delivery)
    assert _TOKEN_A not in rendered
    assert _TOKEN_B not in rendered
    assert "envref" not in rendered


def test_transport_retry_reuses_one_resolution_and_exact_request() -> None:
    resolver = RotatingOtpResolver([_TOKEN_A])
    transport = SequenceTransport(
        [
            OtpHttpResponse(status_code=503, response_bytes=0),
            OtpHttpResponse(status_code=202, response_bytes=0),
        ]
    )
    delivery = _delivery(resolver=resolver, transport=transport)

    _send(delivery)

    assert resolver.calls == 1
    assert transport.requests[0] is transport.requests[1]
    assert resolver.leases[0].closed is True


@pytest.mark.parametrize(
    ("error", "domain_code", "outcome", "operational_code"),
    [
        (
            SecretResolutionRetryableError(),
            "AUTH_OTP_DELIVERY_UNAVAILABLE",
            OtpDeliveryOutcome.UNAVAILABLE,
            "OTP_SECRET_RESOLUTION_RETRYABLE",
        ),
        (
            SecretResolutionFinalError(),
            "AUTH_OTP_DELIVERY_REJECTED",
            OtpDeliveryOutcome.REJECTED,
            "OTP_SECRET_RESOLUTION_FINAL",
        ),
    ],
)
def test_resolution_failure_does_not_call_provider_or_leak_secret_reference(
    error: Exception,
    domain_code: str,
    outcome: OtpDeliveryOutcome,
    operational_code: str,
) -> None:
    resolver = FailingOtpResolver(error)
    transport = SequenceTransport([])
    observer = InMemoryOtpDeliveryObserver()
    delivery = _delivery(
        resolver=resolver,
        transport=transport,
        observer=observer,
    )

    with pytest.raises(DomainError) as captured:
        _send(delivery)

    assert captured.value.code == domain_code
    assert transport.requests == []
    assert resolver.calls == 1
    assert observer.results == [observer.results[0]]
    assert observer.results[0].outcome is outcome
    assert observer.results[0].error_code == operational_code
    rendered = f"{captured.value!s} {captured.value!r} {observer.results!r}"
    assert _SECRET_REF not in rendered
    assert "person@example.test" not in rendered
    assert "123456" not in rendered


def test_environment_reference_reads_rotated_value_without_restart() -> None:
    values = {"KEFE_OTP_PROVIDER_CREDENTIAL": _TOKEN_A}
    environment = EnvironmentSecretReferenceResolver(values.get)
    registry = InMemorySecretResolverRegistry((environment,))
    resolver = RegistryBackedOtpSecretLeaseResolver(
        registry=registry,
        secret_ref=_SECRET_REF,
        lease_ttl_seconds=30,
    )
    now = datetime.now(UTC)

    first = resolver.resolve(at=now, expires_at=now + timedelta(minutes=10))
    first_value = first.use_bytes(lambda value: bytes(value), at=now)
    first.close()
    values["KEFE_OTP_PROVIDER_CREDENTIAL"] = _TOKEN_B
    second = resolver.resolve(at=now, expires_at=now + timedelta(minutes=10))
    second_value = second.use_bytes(lambda value: bytes(value), at=now)
    second.close()

    assert first_value == _TOKEN_A.encode("ascii")
    assert second_value == _TOKEN_B.encode("ascii")
    assert first.closed is second.closed is True
    assert _TOKEN_A not in repr(environment)
    assert _TOKEN_B not in repr(resolver)


def test_production_requires_opaque_reference_and_forbids_direct_token() -> None:
    with pytest.raises(RuntimeError, match="forbids KEFE_OTP_HTTP_BEARER_TOKEN"):
        build_otp_secret_lease_resolver(
            _production_settings(
                otp_delivery_mode="HTTP",
                otp_http_endpoint=_ENDPOINT,
                otp_http_bearer_token=SecretStr(_TOKEN_A),
            )
        )

    settings = _production_settings(
        otp_delivery_mode="HTTP",
        otp_http_endpoint=_ENDPOINT,
        otp_http_secret_ref=SecretStr(_SECRET_REF),
    )
    registry = InMemorySecretResolverRegistry(
        (EnvironmentSecretReferenceResolver(lambda _: _TOKEN_A),)
    )
    delivery = build_otp_delivery(
        settings,
        secret_resolver_registry=registry,
        transport=SequenceTransport([OtpHttpResponse(status_code=202, response_bytes=0)]),
    )

    assert isinstance(delivery, HttpOtpDelivery)
    assert _SECRET_REF not in repr(settings)
    assert _SECRET_REF not in repr(delivery)
    assert _TOKEN_A not in repr(delivery)
