from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from kefe_api.core.errors import DomainError
from kefe_api.core.settings import Settings, get_settings
from kefe_api.main import create_app
from kefe_api.modules.identity.account_models import OtpChannel
from kefe_api.modules.identity.otp_delivery import (
    CapturingOtpDelivery,
    HttpOtpDelivery,
    InMemoryOtpDeliveryObserver,
    OtpDeliveryOutcome,
    OtpHttpRequest,
    OtpHttpResponse,
    OtpHttpTransportError,
    UrllibOtpHttpTransport,
    build_otp_delivery,
)

_ENDPOINT = "https://otp.provider.example/v1/deliveries"
_TOKEN = "managed-provider-bearer-token-01234567890123456789"
_REPLAY_SECRET = "managed-production-replay-secret-0123456789012345"


class SequenceTransport:
    def __init__(self, outcomes: list[OtpHttpResponse | Exception]) -> None:
        self.outcomes = list(outcomes)
        self.requests: list[OtpHttpRequest] = []

    def execute(self, request: OtpHttpRequest) -> OtpHttpResponse:
        self.requests.append(request)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class FakeResponse:
    status = 202

    def __init__(self, body: bytes = b"{}") -> None:
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        del exc_type, exc, traceback

    def read(self, amount: int) -> bytes:
        return self.body[:amount]


class FakeOpener:
    def __init__(self, response: FakeResponse | None = None) -> None:
        self.response = response or FakeResponse()
        self.request = None
        self.timeout = None

    def open(self, request, *, timeout: float):
        self.request = request
        self.timeout = timeout
        return self.response


def _delivery(
    transport,
    observer: InMemoryOtpDeliveryObserver | None = None,
    *,
    max_attempts: int = 2,
) -> HttpOtpDelivery:
    return HttpOtpDelivery(
        endpoint=_ENDPOINT,
        bearer_token=_TOKEN,
        timeout_ms=2_500,
        max_response_bytes=1_024,
        max_attempts=max_attempts,
        transport=transport,
        observer=observer,
    )


def _send(delivery: HttpOtpDelivery):
    delivery_id = uuid4()
    expires_at = datetime.now(UTC) + timedelta(minutes=10)
    delivery.send(
        delivery_id=delivery_id,
        channel=OtpChannel.EMAIL,
        identifier="person@example.test",
        code="123456",
        expires_at=expires_at,
    )
    return delivery_id, expires_at


def test_http_delivery_uses_exact_redacted_idempotent_request_contract() -> None:
    transport = SequenceTransport([OtpHttpResponse(status_code=202, response_bytes=2)])
    observer = InMemoryOtpDeliveryObserver()
    delivery = _delivery(transport, observer)

    delivery_id, expires_at = _send(delivery)

    assert len(transport.requests) == 1
    request = transport.requests[0]
    headers = dict(request.headers)
    payload = json.loads(request.body)
    assert headers == {
        "authorization": f"Bearer {_TOKEN}",
        "content-type": "application/json",
        "idempotency-key": str(delivery_id),
        "user-agent": "kefe-otp-delivery/1",
    }
    assert payload == {
        "channel": "EMAIL",
        "code": "123456",
        "delivery_id": str(delivery_id),
        "expires_at": expires_at.astimezone(UTC).isoformat(timespec="microseconds"),
        "recipient": "person@example.test",
    }
    rendered = repr(request)
    for sensitive in (_ENDPOINT, _TOKEN, "123456", "person@example.test"):
        assert sensitive not in rendered
    assert observer.results[0].outcome is OtpDeliveryOutcome.ACCEPTED
    assert observer.results[0].attempts == 1
    assert "person@example.test" not in repr(observer.results[0].as_operational_dict())


def test_retryable_status_reuses_exact_request_and_idempotency_key() -> None:
    transport = SequenceTransport(
        [
            OtpHttpResponse(status_code=503, response_bytes=0),
            OtpHttpResponse(status_code=202, response_bytes=0),
        ]
    )
    observer = InMemoryOtpDeliveryObserver()
    delivery = _delivery(transport, observer)

    _send(delivery)

    assert len(transport.requests) == 2
    assert transport.requests[0] is transport.requests[1]
    assert len(observer.results) == 1
    assert observer.results[0].outcome is OtpDeliveryOutcome.ACCEPTED
    assert observer.results[0].attempts == 2


def test_retryable_network_failure_exhaustion_is_unavailable() -> None:
    transport = SequenceTransport(
        [
            OtpHttpTransportError("NETWORK_TIMEOUT", retryable=True),
            OtpHttpTransportError("NETWORK_TIMEOUT", retryable=True),
        ]
    )
    observer = InMemoryOtpDeliveryObserver()
    delivery = _delivery(transport, observer)

    with pytest.raises(DomainError) as captured:
        _send(delivery)

    assert captured.value.code == "AUTH_OTP_DELIVERY_UNAVAILABLE"
    assert captured.value.status_code == 503
    assert captured.value.retryable is True
    assert observer.results[0].outcome is OtpDeliveryOutcome.UNAVAILABLE
    assert observer.results[0].attempts == 2
    assert observer.results[0].error_code == "NETWORK_TIMEOUT"


def test_final_provider_rejection_is_not_retried_or_body_exposed() -> None:
    transport = SequenceTransport([OtpHttpResponse(status_code=400, response_bytes=512)])
    observer = InMemoryOtpDeliveryObserver()
    delivery = _delivery(transport, observer, max_attempts=3)

    with pytest.raises(DomainError) as captured:
        _send(delivery)

    assert captured.value.code == "AUTH_OTP_DELIVERY_REJECTED"
    assert captured.value.status_code == 502
    assert captured.value.retryable is False
    assert len(transport.requests) == 1
    assert observer.results[0].outcome is OtpDeliveryOutcome.REJECTED
    assert observer.results[0].status_code == 400


def test_urllib_transport_invokes_post_with_bounded_read_and_timeout() -> None:
    opener = FakeOpener()
    transport = UrllibOtpHttpTransport(opener)
    delivery = _delivery(transport, max_attempts=1)

    delivery_id, _ = _send(delivery)

    assert opener.request is not None
    assert opener.request.full_url == _ENDPOINT
    assert opener.request.get_method() == "POST"
    assert opener.request.headers["Idempotency-key"] == str(delivery_id)
    assert opener.request.headers["Authorization"] == f"Bearer {_TOKEN}"
    assert opener.timeout == 2.5


def test_urllib_transport_rejects_oversized_provider_response_without_body_leak() -> None:
    opener = FakeOpener(FakeResponse(b"x" * 1_025))
    delivery = _delivery(UrllibOtpHttpTransport(opener), max_attempts=1)

    with pytest.raises(DomainError) as captured:
        _send(delivery)

    assert captured.value.code == "AUTH_OTP_DELIVERY_REJECTED"
    assert "x" not in str(captured.value)


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://otp.provider.example/v1/deliveries",
        "https://user:secret@otp.provider.example/v1/deliveries",
        "https://otp.provider.example/v1/deliveries?token=value",
        "https://otp.provider.example/v1/deliveries#fragment",
        "https://127.0.0.1/v1/deliveries",
        "https://localhost/v1/deliveries",
        "https://otp.provider.example/",
        "https://otp.provider.example:8443/v1/deliveries",
    ],
)
def test_unsafe_provider_endpoints_are_rejected(endpoint: str) -> None:
    with pytest.raises(ValueError):
        HttpOtpDelivery(
            endpoint=endpoint,
            bearer_token=_TOKEN,
            timeout_ms=1_000,
            max_response_bytes=1_024,
            max_attempts=1,
            transport=SequenceTransport([]),
        )


def test_account_request_propagates_persisted_challenge_identity_and_expiry() -> None:
    app = create_app()
    client = TestClient(app)
    response = client.post(
        "/v1/auth/otp/request",
        json={"channel": "EMAIL", "identifier": "propagation@example.test"},
    )
    assert response.status_code == 201
    assert isinstance(app.state.otp_delivery, CapturingOtpDelivery)

    metadata = app.state.otp_delivery.metadata_for(
        channel=OtpChannel.EMAIL,
        identifier="propagation@example.test",
    )
    assert metadata is not None
    delivery_id, delivery_expiry = metadata
    body = response.json()
    assert delivery_id == UUID(body["challenge_id"])
    assert delivery_expiry == datetime.fromisoformat(body["expires_at"])


def test_build_otp_delivery_keeps_capture_explicit_and_redacted() -> None:
    delivery = build_otp_delivery(Settings())
    assert isinstance(delivery, CapturingOtpDelivery)
    delivery.send(
        delivery_id=uuid4(),
        channel=OtpChannel.EMAIL,
        identifier="capture@example.test",
        code="654321",
        expires_at=datetime.now(UTC) + timedelta(minutes=10),
    )
    rendered = repr(delivery)
    assert "654321" not in rendered
    assert "capture@example.test" not in rendered


@pytest.mark.parametrize("mode", ["CAPTURE", "DISABLED"])
def test_production_forbids_non_http_delivery_modes(mode: str) -> None:
    settings = Settings(environment="production", otp_delivery_mode=mode)
    with pytest.raises(RuntimeError, match="KEFE_OTP_DELIVERY_MODE=HTTP"):
        build_otp_delivery(settings)


def test_http_mode_requires_endpoint_and_managed_secret() -> None:
    with pytest.raises(RuntimeError, match="KEFE_OTP_HTTP_ENDPOINT"):
        build_otp_delivery(Settings(otp_delivery_mode="HTTP"))


def test_production_http_delivery_builds_with_secretstr_redaction() -> None:
    settings = Settings(
        environment="production",
        otp_delivery_mode="HTTP",
        otp_http_endpoint=_ENDPOINT,
        otp_http_bearer_token=SecretStr(_TOKEN),
    )
    delivery = build_otp_delivery(
        settings,
        transport=SequenceTransport([OtpHttpResponse(status_code=202, response_bytes=0)]),
    )
    assert isinstance(delivery, HttpOtpDelivery)
    assert _TOKEN not in repr(settings)
    assert _TOKEN not in repr(delivery)


def test_full_production_app_rejects_capture_composition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("KEFE_ENVIRONMENT", "production")
    monkeypatch.setenv("KEFE_OTP_DELIVERY_MODE", "CAPTURE")
    monkeypatch.setenv("KEFE_ACCOUNT_MERGE_REPLAY_SECRET", _REPLAY_SECRET)
    get_settings.cache_clear()
    try:
        with pytest.raises(RuntimeError, match="KEFE_OTP_DELIVERY_MODE=HTTP"):
            create_app()
    finally:
        get_settings.cache_clear()


def test_full_production_app_composes_http_delivery_only_when_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("KEFE_ENVIRONMENT", "production")
    monkeypatch.setenv("KEFE_OTP_DELIVERY_MODE", "HTTP")
    monkeypatch.setenv("KEFE_OTP_HTTP_ENDPOINT", _ENDPOINT)
    monkeypatch.setenv("KEFE_OTP_HTTP_BEARER_TOKEN", _TOKEN)
    monkeypatch.setenv("KEFE_ACCOUNT_MERGE_REPLAY_SECRET", _REPLAY_SECRET)
    get_settings.cache_clear()
    try:
        app = create_app()
        assert isinstance(app.state.otp_delivery, HttpOtpDelivery)
        assert _TOKEN not in repr(app.state.otp_delivery)
    finally:
        get_settings.cache_clear()
