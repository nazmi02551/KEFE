from __future__ import annotations

import ipaddress
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from uuid import UUID

from kefe_api.core.errors import DomainError
from kefe_api.core.settings import Settings
from kefe_api.modules.identity.account_models import OtpChannel
from kefe_api.modules.identity.otp_secret_resolution import (
    OtpSecretLeaseResolver,
    StaticOtpSecretLeaseResolver,
    build_otp_secret_lease_resolver,
)
from kefe_api.modules.knowledge.provider_secret_execution import (
    SecretResolutionFinalError,
    SecretResolutionRetryableError,
    SecretResolverRegistry,
)

_RETRYABLE_HTTP_STATUSES = frozenset({408, 425, 429, 500, 502, 503, 504})
_MAX_REQUEST_BYTES = 4_096


class OtpDeliveryOutcome(StrEnum):
    ACCEPTED = "ACCEPTED"
    UNAVAILABLE = "UNAVAILABLE"
    REJECTED = "REJECTED"


@dataclass(frozen=True, slots=True)
class OtpDeliveryOperationalResult:
    outcome: OtpDeliveryOutcome
    channel: OtpChannel
    attempts: int
    status_code: int | None
    error_code: str | None

    def __post_init__(self) -> None:
        if self.attempts < 1:
            raise ValueError("OTP delivery attempts must be positive")
        if self.status_code is not None and not 100 <= self.status_code <= 599:
            raise ValueError("OTP delivery status code is outside the HTTP range")
        if self.outcome is OtpDeliveryOutcome.ACCEPTED:
            if self.error_code is not None:
                raise ValueError("accepted OTP delivery cannot have an error code")
        elif self.error_code is None:
            raise ValueError("failed OTP delivery requires an error code")

    def as_operational_dict(self) -> dict[str, str | int | None]:
        return {
            "outcome": self.outcome.value,
            "channel": self.channel.value,
            "attempts": self.attempts,
            "status_code": self.status_code,
            "error_code": self.error_code,
        }


class OtpDeliveryObserver(Protocol):
    def record(self, result: OtpDeliveryOperationalResult) -> None: ...


class NoOpOtpDeliveryObserver:
    def record(self, result: OtpDeliveryOperationalResult) -> None:
        del result


@dataclass(slots=True)
class InMemoryOtpDeliveryObserver:
    results: list[OtpDeliveryOperationalResult] = field(default_factory=list)

    def record(self, result: OtpDeliveryOperationalResult) -> None:
        self.results.append(result)


@dataclass(frozen=True, slots=True, repr=False)
class OtpHttpRequest:
    endpoint: str
    headers: tuple[tuple[str, str], ...]
    body: bytes
    timeout_seconds: float
    max_response_bytes: int

    def __post_init__(self) -> None:
        if not self.body or len(self.body) > _MAX_REQUEST_BYTES:
            raise ValueError("OTP provider request size is outside the supported range")
        if self.timeout_seconds <= 0:
            raise ValueError("OTP provider timeout must be positive")
        if self.max_response_bytes < 1:
            raise ValueError("OTP provider response budget must be positive")

    def __repr__(self) -> str:
        return (
            "OtpHttpRequest(endpoint=<redacted>, headers=<redacted>, "
            f"body=<redacted:{len(self.body)} bytes>, "
            f"timeout_seconds={self.timeout_seconds!r}, "
            f"max_response_bytes={self.max_response_bytes})"
        )


@dataclass(frozen=True, slots=True)
class OtpHttpResponse:
    status_code: int
    response_bytes: int

    def __post_init__(self) -> None:
        if not 100 <= self.status_code <= 599:
            raise ValueError("OTP provider status code is outside the HTTP range")
        if self.response_bytes < 0:
            raise ValueError("OTP provider response bytes must be non-negative")


class OtpHttpTransportError(Exception):
    def __init__(self, code: str, *, retryable: bool) -> None:
        if not code.strip():
            raise ValueError("OTP transport error code must not be blank")
        self.code = code
        self.retryable = retryable
        super().__init__(code)

    def __repr__(self) -> str:
        return (
            f"OtpHttpTransportError(code={self.code!r}, "
            f"retryable={self.retryable!r})"
        )


class OtpHttpTransport(Protocol):
    def execute(self, request: OtpHttpRequest) -> OtpHttpResponse: ...


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        del req, fp, code, msg, headers, newurl
        return None


class UrllibOtpHttpTransport:
    def __init__(self, opener=None) -> None:
        self._opener = opener or build_opener(_NoRedirectHandler())

    def execute(self, request: OtpHttpRequest) -> OtpHttpResponse:
        outbound = Request(
            request.endpoint,
            data=request.body,
            headers={name: value for name, value in request.headers},
            method="POST",
        )
        try:
            with self._opener.open(outbound, timeout=request.timeout_seconds) as response:
                body = response.read(request.max_response_bytes + 1)
                if len(body) > request.max_response_bytes:
                    raise OtpHttpTransportError(
                        "OTP_PROVIDER_RESPONSE_TOO_LARGE",
                        retryable=False,
                    )
                return OtpHttpResponse(
                    status_code=int(response.status),
                    response_bytes=len(body),
                )
        except HTTPError as exc:
            return OtpHttpResponse(status_code=exc.code, response_bytes=0)
        except OtpHttpTransportError:
            raise
        except (TimeoutError, URLError, OSError) as exc:
            raise OtpHttpTransportError(
                "OTP_PROVIDER_NETWORK_UNAVAILABLE",
                retryable=True,
            ) from exc


class DisabledOtpDelivery:
    def send(
        self,
        *,
        delivery_id: UUID,
        channel: OtpChannel,
        identifier: str,
        code: str,
        expires_at: datetime,
    ) -> None:
        del delivery_id, channel, identifier, code, expires_at
        raise DomainError(
            "AUTH_OTP_DELIVERY_UNAVAILABLE",
            "OTP delivery is not configured",
            503,
            retryable=True,
        )


@dataclass(slots=True, repr=False)
class CapturingOtpDelivery:
    """Development/test adapter. Never expose captured codes through HTTP or repr."""

    deliveries: dict[tuple[str, str], str] = field(default_factory=dict)
    metadata: dict[tuple[str, str], tuple[UUID, datetime]] = field(default_factory=dict)

    def send(
        self,
        *,
        delivery_id: UUID,
        channel: OtpChannel,
        identifier: str,
        code: str,
        expires_at: datetime,
    ) -> None:
        key = (channel.value, identifier)
        self.deliveries[key] = code
        self.metadata[key] = (delivery_id, expires_at)

    def code_for(self, *, channel: OtpChannel, identifier: str) -> str | None:
        return self.deliveries.get((channel.value, identifier))

    def metadata_for(
        self,
        *,
        channel: OtpChannel,
        identifier: str,
    ) -> tuple[UUID, datetime] | None:
        return self.metadata.get((channel.value, identifier))

    def __repr__(self) -> str:
        return f"CapturingOtpDelivery(deliveries=<redacted:{len(self.deliveries)}>)"


class HttpOtpDelivery:
    def __init__(
        self,
        *,
        endpoint: str,
        timeout_ms: int,
        max_response_bytes: int,
        max_attempts: int,
        secret_resolver: OtpSecretLeaseResolver | None = None,
        bearer_token: str | None = None,
        transport: OtpHttpTransport | None = None,
        observer: OtpDeliveryObserver | None = None,
    ) -> None:
        self._endpoint = self._validated_endpoint(endpoint)
        if (secret_resolver is None) == (bearer_token is None):
            raise ValueError(
                "OTP delivery requires exactly one secret resolver or bearer token"
            )
        self._secret_resolver = secret_resolver or StaticOtpSecretLeaseResolver(
            bearer_token or "",
            lease_ttl_seconds=30,
        )
        if not 100 <= timeout_ms <= 10_000:
            raise ValueError("OTP provider timeout is outside the supported range")
        if not 1 <= max_response_bytes <= 65_536:
            raise ValueError("OTP provider response budget is outside the supported range")
        if not 1 <= max_attempts <= 3:
            raise ValueError("OTP provider attempt limit is outside the supported range")
        self._timeout_seconds = timeout_ms / 1_000
        self._max_response_bytes = max_response_bytes
        self._max_attempts = max_attempts
        self._transport = transport or UrllibOtpHttpTransport()
        self._observer = observer or NoOpOtpDeliveryObserver()

    def send(
        self,
        *,
        delivery_id: UUID,
        channel: OtpChannel,
        identifier: str,
        code: str,
        expires_at: datetime,
    ) -> None:
        resolved_at = datetime.now(UTC)
        try:
            lease = self._secret_resolver.resolve(
                at=resolved_at,
                expires_at=expires_at,
            )
        except SecretResolutionRetryableError as exc:
            self._record(
                OtpDeliveryOutcome.UNAVAILABLE,
                channel,
                1,
                None,
                "OTP_SECRET_RESOLUTION_RETRYABLE",
            )
            raise self._unavailable_error() from exc
        except SecretResolutionFinalError as exc:
            self._record(
                OtpDeliveryOutcome.REJECTED,
                channel,
                1,
                None,
                "OTP_SECRET_RESOLUTION_FINAL",
            )
            raise self._rejected_error() from exc
        except Exception as exc:
            self._record(
                OtpDeliveryOutcome.REJECTED,
                channel,
                1,
                None,
                "OTP_SECRET_RESOLUTION_UNEXPECTED",
            )
            raise self._rejected_error() from exc

        try:
            try:
                lease.use_bytes(
                    lambda secret: self._send_with_secret(
                        secret=secret,
                        delivery_id=delivery_id,
                        channel=channel,
                        identifier=identifier,
                        code=code,
                        expires_at=expires_at,
                    ),
                    at=resolved_at,
                )
            except (RuntimeError, ValueError) as exc:
                self._record(
                    OtpDeliveryOutcome.REJECTED,
                    channel,
                    1,
                    None,
                    "OTP_SECRET_MATERIAL_INVALID",
                )
                raise self._rejected_error() from exc
        finally:
            lease.close()

    def _send_with_secret(
        self,
        *,
        secret: memoryview,
        delivery_id: UUID,
        channel: OtpChannel,
        identifier: str,
        code: str,
        expires_at: datetime,
    ) -> None:
        request = self._request(
            secret=secret,
            delivery_id=delivery_id,
            channel=channel,
            identifier=identifier,
            code=code,
            expires_at=expires_at,
        )
        for attempt in range(1, self._max_attempts + 1):
            try:
                response = self._transport.execute(request)
            except OtpHttpTransportError as exc:
                if exc.retryable and attempt < self._max_attempts:
                    continue
                if exc.retryable:
                    self._record(
                        OtpDeliveryOutcome.UNAVAILABLE,
                        channel,
                        attempt,
                        None,
                        exc.code,
                    )
                    raise self._unavailable_error() from exc
                self._record(
                    OtpDeliveryOutcome.REJECTED,
                    channel,
                    attempt,
                    None,
                    exc.code,
                )
                raise self._rejected_error() from exc

            if 200 <= response.status_code <= 299:
                self._record(
                    OtpDeliveryOutcome.ACCEPTED,
                    channel,
                    attempt,
                    response.status_code,
                    None,
                )
                return
            if response.status_code in _RETRYABLE_HTTP_STATUSES:
                if attempt < self._max_attempts:
                    continue
                self._record(
                    OtpDeliveryOutcome.UNAVAILABLE,
                    channel,
                    attempt,
                    response.status_code,
                    "OTP_PROVIDER_RETRYABLE_STATUS",
                )
                raise self._unavailable_error()

            self._record(
                OtpDeliveryOutcome.REJECTED,
                channel,
                attempt,
                response.status_code,
                "OTP_PROVIDER_REJECTED_STATUS",
            )
            raise self._rejected_error()

        raise AssertionError("OTP delivery attempt loop exited unexpectedly")

    def _request(
        self,
        *,
        secret: memoryview,
        delivery_id: UUID,
        channel: OtpChannel,
        identifier: str,
        code: str,
        expires_at: datetime,
    ) -> OtpHttpRequest:
        bearer_token = self._validated_secret(secret)
        payload = json.dumps(
            {
                "channel": channel.value,
                "code": code,
                "delivery_id": str(delivery_id),
                "expires_at": expires_at.astimezone(UTC).isoformat(
                    timespec="microseconds"
                ),
                "recipient": identifier,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return OtpHttpRequest(
            endpoint=self._endpoint,
            headers=(
                ("authorization", f"Bearer {bearer_token}"),
                ("content-type", "application/json"),
                ("idempotency-key", str(delivery_id)),
                ("user-agent", "kefe-otp-delivery/1"),
            ),
            body=payload,
            timeout_seconds=self._timeout_seconds,
            max_response_bytes=self._max_response_bytes,
        )

    def _record(
        self,
        outcome: OtpDeliveryOutcome,
        channel: OtpChannel,
        attempts: int,
        status_code: int | None,
        error_code: str | None,
    ) -> None:
        self._observer.record(
            OtpDeliveryOperationalResult(
                outcome=outcome,
                channel=channel,
                attempts=attempts,
                status_code=status_code,
                error_code=error_code,
            )
        )

    @staticmethod
    def _unavailable_error() -> DomainError:
        return DomainError(
            "AUTH_OTP_DELIVERY_UNAVAILABLE",
            "OTP delivery provider is temporarily unavailable",
            503,
            retryable=True,
        )

    @staticmethod
    def _rejected_error() -> DomainError:
        return DomainError(
            "AUTH_OTP_DELIVERY_REJECTED",
            "OTP delivery provider rejected the request",
            502,
            retryable=False,
        )

    @staticmethod
    def _validated_secret(value: memoryview) -> str:
        if not value or len(value) < 32:
            raise ValueError(
                "OTP provider bearer token must contain at least 32 unpadded characters"
            )
        try:
            decoded = bytes(value).decode("ascii")
        except UnicodeDecodeError as exc:
            raise ValueError("OTP provider bearer token must be ASCII") from exc
        if decoded != decoded.strip() or "\r" in decoded or "\n" in decoded:
            raise ValueError(
                "OTP provider bearer token must contain at least 32 unpadded characters"
            )
        return decoded

    @staticmethod
    def _validated_endpoint(value: str) -> str:
        if not value or value != value.strip() or any(ord(char) < 32 for char in value):
            raise ValueError("OTP provider endpoint is invalid")
        try:
            parsed = urlsplit(value)
            port = parsed.port
        except ValueError as exc:
            raise ValueError("OTP provider endpoint is invalid") from exc
        if parsed.scheme != "https":
            raise ValueError("OTP provider endpoint must use https")
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("OTP provider endpoint cannot contain userinfo")
        if parsed.hostname is None:
            raise ValueError("OTP provider endpoint requires a hostname")
        if parsed.query or parsed.fragment:
            raise ValueError("OTP provider endpoint cannot contain query or fragment")
        if port not in (None, 443):
            raise ValueError("OTP provider endpoint port must be 443")
        if not parsed.path.startswith("/") or parsed.path == "/":
            raise ValueError("OTP provider endpoint requires an explicit path")
        try:
            parsed.hostname.encode("ascii")
        except UnicodeEncodeError as exc:
            raise ValueError("OTP provider hostname must be ASCII") from exc
        host = parsed.hostname.lower()
        if host == "localhost" or host.endswith(".local") or "." not in host:
            raise ValueError("OTP provider hostname must be a public DNS name")
        try:
            ipaddress.ip_address(host)
        except ValueError:
            pass
        else:
            raise ValueError("OTP provider endpoint cannot use an IP literal")
        return value

    def __repr__(self) -> str:
        return (
            "HttpOtpDelivery(endpoint=<redacted>, secret_resolver=<redacted>, "
            f"timeout_seconds={self._timeout_seconds!r}, "
            f"max_response_bytes={self._max_response_bytes}, "
            f"max_attempts={self._max_attempts})"
        )


def build_otp_delivery(
    settings: Settings,
    *,
    transport: OtpHttpTransport | None = None,
    observer: OtpDeliveryObserver | None = None,
    secret_resolver_registry: SecretResolverRegistry | None = None,
):
    mode = settings.otp_delivery_mode
    production = settings.environment.strip().lower() == "production"
    if production and mode != "HTTP":
        raise RuntimeError("production requires KEFE_OTP_DELIVERY_MODE=HTTP")
    if mode == "CAPTURE":
        return CapturingOtpDelivery()
    if mode == "DISABLED":
        return DisabledOtpDelivery()

    endpoint = settings.otp_http_endpoint
    if endpoint is None:
        raise RuntimeError("HTTP OTP delivery requires KEFE_OTP_HTTP_ENDPOINT")
    secret_resolver = build_otp_secret_lease_resolver(
        settings,
        registry=secret_resolver_registry,
    )
    return HttpOtpDelivery(
        endpoint=endpoint,
        secret_resolver=secret_resolver,
        timeout_ms=settings.otp_http_timeout_ms,
        max_response_bytes=settings.otp_http_max_response_bytes,
        max_attempts=settings.otp_http_max_attempts,
        transport=transport,
        observer=observer,
    )
