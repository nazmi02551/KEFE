from __future__ import annotations

import ipaddress
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from time import monotonic_ns
from types import MappingProxyType
from typing import Protocol, TypeVar
from urllib.parse import parse_qsl, urljoin, urlsplit

from kefe_api.modules.knowledge.source_identity import require_versioned_adapter_code

T = TypeVar("T")

_EVIDENCE_REFERENCE = re.compile(r"^(?:docref|evidence)://[A-Za-z0-9._/@:+-]+$")
_MEDIA_TYPE = re.compile(r"^[a-z0-9][a-z0-9!#$&^_.+-]*/[a-z0-9][a-z0-9!#$&^_.+-]*$")
_SAFE_PUBLIC_HEADERS = frozenset(
    {"accept", "user-agent", "if-none-match", "if-modified-since"}
)
_FORBIDDEN_QUERY_NAMES = frozenset(
    {
        "access_token",
        "api_key",
        "apikey",
        "auth",
        "authorization",
        "key",
        "password",
        "secret",
        "sig",
        "signature",
        "token",
    }
)
_REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})
_RETRYABLE_STATUSES = frozenset({408, 425, 429, 500, 502, 503, 504})

MIN_TIMEOUT_MS = 50
MAX_CONNECT_OR_READ_TIMEOUT_MS = 30_000
MAX_TOTAL_TIMEOUT_MS = 120_000
MAX_RESPONSE_BYTES = 10 * 1024 * 1024
MAX_REDIRECT_HOPS = 5


def _require_text(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} must not be blank")


def _canonical_origin(value: str) -> str:
    _require_text(value, "origin")
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as exc:
        raise ValueError("origin is invalid") from exc
    if parsed.scheme != "https":
        raise ValueError("origin must use https")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("origin cannot contain userinfo")
    if parsed.hostname is None:
        raise ValueError("origin requires a hostname")
    try:
        parsed.hostname.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError("origin hostname must be ASCII") from exc
    host = parsed.hostname.lower()
    if "*" in host:
        raise ValueError("origin wildcards are forbidden")
    if port not in (None, 443):
        raise ValueError("origin port must be 443")
    if parsed.path not in ("", "/") or parsed.query or parsed.fragment:
        raise ValueError("origin cannot contain path, query or fragment")
    rendered_host = f"[{host}]" if ":" in host else host
    return f"https://{rendered_host}"


def _normalize_query_name(value: str) -> str:
    return value.strip().lower().replace("-", "_")


class ProviderHttpMethod(StrEnum):
    GET = "GET"
    HEAD = "HEAD"


@dataclass(frozen=True, slots=True)
class ProviderAdoptionProfile:
    adapter_code: str
    allowed_origins: tuple[str, ...]
    allowed_methods: tuple[ProviderHttpMethod, ...]
    allowed_media_types: tuple[str, ...]
    connect_timeout_ms: int
    read_timeout_ms: int
    total_timeout_ms: int
    max_response_bytes: int
    max_redirect_hops: int
    terms_evidence_ref: str
    rate_limit_evidence_ref: str

    def __post_init__(self) -> None:
        require_versioned_adapter_code(self.adapter_code)
        if not self.allowed_origins:
            raise ValueError("at least one allowed origin is required")
        canonical_origins = tuple(_canonical_origin(item) for item in self.allowed_origins)
        if canonical_origins != tuple(sorted(set(canonical_origins))):
            raise ValueError("allowed origins must be canonical, unique and sorted")
        if not self.allowed_methods:
            raise ValueError("at least one HTTP method is required")
        if self.allowed_methods != tuple(
            sorted(set(self.allowed_methods), key=lambda item: item.value)
        ):
            raise ValueError("allowed methods must be unique and sorted")
        if not self.allowed_media_types:
            raise ValueError("at least one response media type is required")
        normalized_media_types = tuple(item.strip().lower() for item in self.allowed_media_types)
        if any(_MEDIA_TYPE.fullmatch(item) is None for item in normalized_media_types):
            raise ValueError("response media types must be exact lowercase types")
        if normalized_media_types != tuple(sorted(set(normalized_media_types))):
            raise ValueError("response media types must be unique and sorted")
        if not MIN_TIMEOUT_MS <= self.connect_timeout_ms <= MAX_CONNECT_OR_READ_TIMEOUT_MS:
            raise ValueError("connect timeout is outside the supported range")
        if not MIN_TIMEOUT_MS <= self.read_timeout_ms <= MAX_CONNECT_OR_READ_TIMEOUT_MS:
            raise ValueError("read timeout is outside the supported range")
        if not MIN_TIMEOUT_MS <= self.total_timeout_ms <= MAX_TOTAL_TIMEOUT_MS:
            raise ValueError("total timeout is outside the supported range")
        if self.total_timeout_ms < max(self.connect_timeout_ms, self.read_timeout_ms):
            raise ValueError("total timeout cannot be below connect or read timeout")
        if not 1 <= self.max_response_bytes <= MAX_RESPONSE_BYTES:
            raise ValueError("response byte budget is outside the supported range")
        if not 0 <= self.max_redirect_hops <= MAX_REDIRECT_HOPS:
            raise ValueError("redirect budget is outside the supported range")
        for value, field_name in (
            (self.terms_evidence_ref, "terms_evidence_ref"),
            (self.rate_limit_evidence_ref, "rate_limit_evidence_ref"),
        ):
            _require_text(value, field_name)
            if _EVIDENCE_REFERENCE.fullmatch(value) is None:
                raise ValueError(f"{field_name} must be an opaque evidence reference")

    @property
    def immutable_configuration(self) -> tuple[object, ...]:
        return (
            self.adapter_code,
            self.allowed_origins,
            self.allowed_methods,
            self.allowed_media_types,
            self.connect_timeout_ms,
            self.read_timeout_ms,
            self.total_timeout_ms,
            self.max_response_bytes,
            self.max_redirect_hops,
            self.terms_evidence_ref,
            self.rate_limit_evidence_ref,
        )


class ProviderAdoptionRegistry(Protocol):
    def get(self, adapter_code: str) -> ProviderAdoptionProfile: ...


class InMemoryProviderAdoptionRegistry:
    def __init__(self, profiles: tuple[ProviderAdoptionProfile, ...] = ()) -> None:
        profile_map: dict[str, ProviderAdoptionProfile] = {}
        for profile in profiles:
            existing = profile_map.get(profile.adapter_code)
            if existing is not None:
                if existing.immutable_configuration != profile.immutable_configuration:
                    raise ValueError("conflicting provider adoption profile")
                raise ValueError("duplicate provider adoption profile")
            profile_map[profile.adapter_code] = profile
        self._profiles = MappingProxyType(profile_map)

    def get(self, adapter_code: str) -> ProviderAdoptionProfile:
        require_versioned_adapter_code(adapter_code)
        try:
            return self._profiles[adapter_code]
        except KeyError as exc:
            raise KeyError(adapter_code) from exc


class SensitiveHttpHeaderAccess(Protocol):
    def use_headers(
        self,
        callback: Callable[[tuple[tuple[str, memoryview], ...]], T],
    ) -> T: ...


@dataclass(frozen=True, slots=True, repr=False, eq=False)
class ProviderHttpCredentialBinding:
    credential_origin: str
    headers: SensitiveHttpHeaderAccess = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.credential_origin != _canonical_origin(self.credential_origin):
            raise ValueError("credential_origin must be canonical")

    def __repr__(self) -> str:
        return (
            "ProviderHttpCredentialBinding("
            f"credential_origin={self.credential_origin!r}, headers=<REDACTED>)"
        )


@dataclass(frozen=True, slots=True, repr=False)
class OutboundHttpRequest:
    adapter_code: str
    method: ProviderHttpMethod
    url: str
    public_headers: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        require_versioned_adapter_code(self.adapter_code)
        _require_text(self.url, "url")
        normalized_names: list[str] = []
        for name, value in self.public_headers:
            normalized = name.strip().lower()
            if normalized not in _SAFE_PUBLIC_HEADERS:
                raise ValueError("public header is not allowed")
            if normalized in normalized_names:
                raise ValueError("duplicate public header")
            _require_text(value, "public header value")
            if "\r" in value or "\n" in value:
                raise ValueError("public header value contains a line break")
            normalized_names.append(normalized)
        if normalized_names != sorted(normalized_names):
            raise ValueError("public headers must be sorted by lowercase name")

    def __repr__(self) -> str:
        return (
            "OutboundHttpRequest("
            f"adapter_code={self.adapter_code!r}, method={self.method.value!r}, "
            "url=<redacted>, public_headers=<redacted>)"
        )


@dataclass(frozen=True, slots=True, repr=False)
class PinnedOutboundHttpRequest:
    adapter_code: str
    method: ProviderHttpMethod
    host: str
    port: int
    target_ip: str
    request_target: str
    public_headers: tuple[tuple[str, str], ...]
    connect_timeout_ms: int
    read_timeout_ms: int
    max_response_bytes: int
    sensitive_headers: SensitiveHttpHeaderAccess | None = field(
        default=None,
        repr=False,
        compare=False,
    )

    def __repr__(self) -> str:
        return (
            "PinnedOutboundHttpRequest("
            f"adapter_code={self.adapter_code!r}, method={self.method.value!r}, "
            f"host={self.host!r}, port={self.port}, target_ip=<redacted>, "
            "request_target=<redacted>, public_headers=<redacted>, "
            "sensitive_headers=<redacted>)"
        )


@dataclass(frozen=True, slots=True, repr=False)
class RawHttpResponse:
    status_code: int
    headers: tuple[tuple[str, str], ...]
    body: bytes
    elapsed_ms: int

    def __post_init__(self) -> None:
        if not 100 <= self.status_code <= 599:
            raise ValueError("status code is outside the HTTP range")
        if self.elapsed_ms < 0:
            raise ValueError("elapsed_ms must be non-negative")
        normalized: list[str] = []
        for name, value in self.headers:
            header_name = name.strip().lower()
            _require_text(header_name, "response header name")
            if header_name in normalized:
                raise ValueError("duplicate response header")
            if "\r" in value or "\n" in value:
                raise ValueError("response header contains a line break")
            normalized.append(header_name)
        if normalized != sorted(normalized):
            raise ValueError("response headers must be sorted by lowercase name")

    def header(self, name: str) -> str | None:
        expected = name.lower()
        for header_name, value in self.headers:
            if header_name.lower() == expected:
                return value
        return None

    def __repr__(self) -> str:
        return (
            "RawHttpResponse("
            f"status_code={self.status_code}, headers=<redacted>, "
            f"body=<redacted:{len(self.body)} bytes>, elapsed_ms={self.elapsed_ms})"
        )


class ProviderDnsResolver(Protocol):
    def resolve(self, host: str) -> tuple[str, ...]: ...


class PinnedHttpBackend(Protocol):
    def execute(self, request: PinnedOutboundHttpRequest) -> RawHttpResponse: ...


class UnconfiguredProviderDnsResolver:
    def resolve(self, host: str) -> tuple[str, ...]:
        del host
        raise RetryableProviderHttpError("PROVIDER_HTTP_DNS_UNAVAILABLE")


class UnconfiguredPinnedHttpBackend:
    def execute(self, request: PinnedOutboundHttpRequest) -> RawHttpResponse:
        del request
        raise FinalProviderHttpError("PROVIDER_HTTP_BACKEND_UNCONFIGURED")


class ProviderHttpError(Exception):
    def __init__(self, code: str) -> None:
        _require_text(code, "provider HTTP error code")
        self.code = code
        super().__init__(code)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(code={self.code!r})"


class RetryableProviderHttpError(ProviderHttpError):
    pass


class FinalProviderHttpError(ProviderHttpError):
    pass


class ProviderHttpOutcome(StrEnum):
    SUCCEEDED = "SUCCEEDED"
    NOT_MODIFIED = "NOT_MODIFIED"
    RETRYABLE_FAILURE = "RETRYABLE_FAILURE"
    FINAL_FAILURE = "FINAL_FAILURE"


@dataclass(frozen=True, slots=True)
class ProviderHttpOperationalResult:
    outcome: ProviderHttpOutcome
    adapter_code: str
    method: ProviderHttpMethod
    status_code: int | None
    redirect_hops: int
    response_bytes: int
    elapsed_ms: int
    error_code: str | None

    def __post_init__(self) -> None:
        require_versioned_adapter_code(self.adapter_code)
        if self.status_code is not None and not 100 <= self.status_code <= 599:
            raise ValueError("status_code is outside the HTTP range")
        if self.redirect_hops < 0 or self.response_bytes < 0 or self.elapsed_ms < 0:
            raise ValueError("operational counters must be non-negative")
        if self.outcome in {ProviderHttpOutcome.SUCCEEDED, ProviderHttpOutcome.NOT_MODIFIED}:
            if self.error_code is not None:
                raise ValueError("successful HTTP result cannot have error_code")
        elif self.error_code is None:
            raise ValueError("failed HTTP result requires error_code")

    def as_operational_dict(self) -> dict[str, str | int | None]:
        return {
            "outcome": self.outcome.value,
            "adapter_code": self.adapter_code,
            "method": self.method.value,
            "status_code": self.status_code,
            "redirect_hops": self.redirect_hops,
            "response_bytes": self.response_bytes,
            "elapsed_ms": self.elapsed_ms,
            "error_code": self.error_code,
        }


class ProviderHttpObserver(Protocol):
    def record(self, result: ProviderHttpOperationalResult) -> None: ...


class NoOpProviderHttpObserver:
    def record(self, result: ProviderHttpOperationalResult) -> None:
        del result


class InMemoryProviderHttpObserver:
    def __init__(self) -> None:
        self.results: list[ProviderHttpOperationalResult] = []

    def record(self, result: ProviderHttpOperationalResult) -> None:
        self.results.append(result)


@dataclass(frozen=True, slots=True, repr=False)
class ProviderHttpResponse:
    status_code: int
    media_type: str | None
    body: bytes
    redirect_hops: int
    elapsed_ms: int

    def __repr__(self) -> str:
        return (
            "ProviderHttpResponse("
            f"status_code={self.status_code}, media_type={self.media_type!r}, "
            f"body=<redacted:{len(self.body)} bytes>, "
            f"redirect_hops={self.redirect_hops}, elapsed_ms={self.elapsed_ms})"
        )


class ControlledProviderHttpTransport:
    def __init__(
        self,
        *,
        adoption_registry: ProviderAdoptionRegistry,
        dns_resolver: ProviderDnsResolver,
        backend: PinnedHttpBackend,
        observer: ProviderHttpObserver,
        monotonic_clock=monotonic_ns,
    ) -> None:
        self._adoption_registry = adoption_registry
        self._dns_resolver = dns_resolver
        self._backend = backend
        self._observer = observer
        self._monotonic_clock = monotonic_clock

    def execute(
        self,
        request: OutboundHttpRequest,
        *,
        credential: ProviderHttpCredentialBinding | None = None,
    ) -> ProviderHttpResponse:
        started_ns = self._monotonic_clock()
        status_code: int | None = None
        redirect_hops = 0
        response_bytes = 0
        elapsed_ms = 0
        try:
            try:
                profile = self._adoption_registry.get(request.adapter_code)
            except KeyError as exc:
                raise FinalProviderHttpError(
                    "PROVIDER_HTTP_PROFILE_NOT_REGISTERED"
                ) from exc
            if request.method not in profile.allowed_methods:
                raise FinalProviderHttpError("PROVIDER_HTTP_METHOD_NOT_ALLOWED")
            if (
                credential is not None
                and credential.credential_origin not in profile.allowed_origins
            ):
                raise FinalProviderHttpError("PROVIDER_HTTP_AUTH_ORIGIN_NOT_ALLOWED")

            current_url = request.url
            while True:
                origin, host, port, request_target = self._validate_url(
                    profile,
                    current_url,
                )
                sensitive_headers = None
                if credential is not None:
                    if origin != credential.credential_origin:
                        raise FinalProviderHttpError(
                            "PROVIDER_HTTP_AUTH_REDIRECT_BLOCKED"
                        )
                    sensitive_headers = credential.headers
                target_ip = self._resolve_public_target(host)
                pinned = PinnedOutboundHttpRequest(
                    adapter_code=request.adapter_code,
                    method=request.method,
                    host=host,
                    port=port,
                    target_ip=target_ip,
                    request_target=request_target,
                    public_headers=request.public_headers,
                    connect_timeout_ms=profile.connect_timeout_ms,
                    read_timeout_ms=profile.read_timeout_ms,
                    max_response_bytes=profile.max_response_bytes,
                    sensitive_headers=sensitive_headers,
                )
                try:
                    raw = self._backend.execute(pinned)
                except ProviderHttpError:
                    raise
                except TimeoutError as exc:
                    raise RetryableProviderHttpError("PROVIDER_HTTP_TIMEOUT") from exc
                except OSError as exc:
                    raise RetryableProviderHttpError("PROVIDER_HTTP_UNAVAILABLE") from exc
                except Exception as exc:
                    raise RetryableProviderHttpError("PROVIDER_HTTP_UNAVAILABLE") from exc

                status_code = raw.status_code
                response_bytes = len(raw.body)
                elapsed_ms += raw.elapsed_ms
                if elapsed_ms > profile.total_timeout_ms:
                    raise RetryableProviderHttpError(
                        "PROVIDER_HTTP_TOTAL_BUDGET_EXCEEDED"
                    )

                if raw.status_code in _REDIRECT_STATUSES:
                    if redirect_hops >= profile.max_redirect_hops:
                        raise FinalProviderHttpError("PROVIDER_HTTP_REDIRECT_BLOCKED")
                    location = raw.header("location")
                    if location is None or not location.strip():
                        raise FinalProviderHttpError("PROVIDER_HTTP_REDIRECT_INVALID")
                    current_url = urljoin(current_url, location)
                    redirect_hops += 1
                    continue

                self._enforce_status(raw.status_code)
                media_type = self._enforce_response(profile, request.method, raw)
                outcome = (
                    ProviderHttpOutcome.NOT_MODIFIED
                    if raw.status_code == 304
                    else ProviderHttpOutcome.SUCCEEDED
                )
                elapsed_ms = max(
                    elapsed_ms,
                    int((self._monotonic_clock() - started_ns) / 1_000_000),
                )
                self._observer.record(
                    ProviderHttpOperationalResult(
                        outcome=outcome,
                        adapter_code=request.adapter_code,
                        method=request.method,
                        status_code=raw.status_code,
                        redirect_hops=redirect_hops,
                        response_bytes=len(raw.body),
                        elapsed_ms=elapsed_ms,
                        error_code=None,
                    )
                )
                return ProviderHttpResponse(
                    status_code=raw.status_code,
                    media_type=media_type,
                    body=raw.body,
                    redirect_hops=redirect_hops,
                    elapsed_ms=elapsed_ms,
                )
        except RetryableProviderHttpError as exc:
            elapsed_ms = max(
                elapsed_ms,
                int((self._monotonic_clock() - started_ns) / 1_000_000),
            )
            self._observer.record(
                ProviderHttpOperationalResult(
                    outcome=ProviderHttpOutcome.RETRYABLE_FAILURE,
                    adapter_code=request.adapter_code,
                    method=request.method,
                    status_code=status_code,
                    redirect_hops=redirect_hops,
                    response_bytes=response_bytes,
                    elapsed_ms=elapsed_ms,
                    error_code=exc.code,
                )
            )
            raise
        except FinalProviderHttpError as exc:
            elapsed_ms = max(
                elapsed_ms,
                int((self._monotonic_clock() - started_ns) / 1_000_000),
            )
            self._observer.record(
                ProviderHttpOperationalResult(
                    outcome=ProviderHttpOutcome.FINAL_FAILURE,
                    adapter_code=request.adapter_code,
                    method=request.method,
                    status_code=status_code,
                    redirect_hops=redirect_hops,
                    response_bytes=response_bytes,
                    elapsed_ms=elapsed_ms,
                    error_code=exc.code,
                )
            )
            raise

    def _validate_url(
        self,
        profile: ProviderAdoptionProfile,
        url: str,
    ) -> tuple[str, str, int, str]:
        try:
            parsed = urlsplit(url)
            port = parsed.port
        except ValueError as exc:
            raise FinalProviderHttpError("PROVIDER_HTTP_URL_NOT_ALLOWED") from exc
        if parsed.scheme != "https":
            raise FinalProviderHttpError("PROVIDER_HTTP_URL_NOT_ALLOWED")
        if parsed.username is not None or parsed.password is not None:
            raise FinalProviderHttpError("PROVIDER_HTTP_URL_NOT_ALLOWED")
        if parsed.hostname is None or parsed.fragment:
            raise FinalProviderHttpError("PROVIDER_HTTP_URL_NOT_ALLOWED")
        try:
            parsed.hostname.encode("ascii")
        except UnicodeEncodeError as exc:
            raise FinalProviderHttpError("PROVIDER_HTTP_URL_NOT_ALLOWED") from exc
        host = parsed.hostname.lower()
        if "*" in host or port not in (None, 443):
            raise FinalProviderHttpError("PROVIDER_HTTP_URL_NOT_ALLOWED")
        rendered_host = f"[{host}]" if ":" in host else host
        origin = f"https://{rendered_host}"
        if origin not in profile.allowed_origins:
            raise FinalProviderHttpError("PROVIDER_HTTP_URL_NOT_ALLOWED")
        for name, _ in parse_qsl(parsed.query, keep_blank_values=True):
            if _normalize_query_name(name) in _FORBIDDEN_QUERY_NAMES:
                raise FinalProviderHttpError(
                    "PROVIDER_HTTP_CREDENTIAL_QUERY_FORBIDDEN"
                )
        path = parsed.path or "/"
        request_target = f"{path}?{parsed.query}" if parsed.query else path
        return origin, host, 443, request_target

    def _resolve_public_target(self, host: str) -> str:
        try:
            answers = self._dns_resolver.resolve(host)
        except ProviderHttpError:
            raise
        except Exception as exc:
            raise RetryableProviderHttpError("PROVIDER_HTTP_DNS_UNAVAILABLE") from exc
        if not answers:
            raise RetryableProviderHttpError("PROVIDER_HTTP_DNS_UNAVAILABLE")
        parsed_addresses: list[ipaddress.IPv4Address | ipaddress.IPv6Address] = []
        for answer in answers:
            try:
                address = ipaddress.ip_address(answer)
            except ValueError as exc:
                raise FinalProviderHttpError("PROVIDER_HTTP_DNS_INVALID") from exc
            if (
                not address.is_global
                or address.is_loopback
                or address.is_private
                or address.is_link_local
                or address.is_multicast
                or address.is_reserved
                or address.is_unspecified
            ):
                raise FinalProviderHttpError("PROVIDER_HTTP_TARGET_NOT_PUBLIC")
            parsed_addresses.append(address)
        selected = sorted(
            set(parsed_addresses),
            key=lambda address: (address.version, address.packed),
        )[0]
        return str(selected)

    @staticmethod
    def _enforce_status(status_code: int) -> None:
        if 200 <= status_code <= 299 or status_code == 304:
            return
        if status_code in _RETRYABLE_STATUSES:
            raise RetryableProviderHttpError("PROVIDER_HTTP_STATUS_RETRYABLE")
        raise FinalProviderHttpError("PROVIDER_HTTP_STATUS_FINAL")

    @staticmethod
    def _enforce_response(
        profile: ProviderAdoptionProfile,
        method: ProviderHttpMethod,
        response: RawHttpResponse,
    ) -> str | None:
        if len(response.body) > profile.max_response_bytes:
            raise FinalProviderHttpError("PROVIDER_HTTP_RESPONSE_TOO_LARGE")
        content_type = response.header("content-type")
        media_type = None
        if content_type is not None:
            media_type = content_type.split(";", 1)[0].strip().lower()
            if _MEDIA_TYPE.fullmatch(media_type) is None:
                raise FinalProviderHttpError("PROVIDER_HTTP_RESPONSE_INVALID")
            if media_type not in profile.allowed_media_types:
                raise FinalProviderHttpError(
                    "PROVIDER_HTTP_MEDIA_TYPE_NOT_ALLOWED"
                )
        requires_media_type = (
            method is ProviderHttpMethod.GET
            and response.status_code not in {204, 304}
            and bool(response.body)
        )
        if requires_media_type and media_type is None:
            raise FinalProviderHttpError("PROVIDER_HTTP_MEDIA_TYPE_NOT_ALLOWED")
        return media_type
