from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Protocol, TypeVar
from urllib.parse import urlsplit

from kefe_api.modules.knowledge.provider_http_transport import (
    ControlledProviderHttpTransport,
    FinalProviderHttpError,
    OutboundHttpRequest,
    ProviderHttpCredentialBinding,
    ProviderHttpError,
    ProviderHttpResponse,
    SensitiveHttpHeaderAccess,
)
from kefe_api.modules.knowledge.provider_secret_execution import SecretAccess
from kefe_api.modules.knowledge.source_identity import require_versioned_adapter_code

T = TypeVar("T")

_EVIDENCE_REFERENCE = re.compile(r"^(?:docref|evidence)://[A-Za-z0-9._/@:+-]+$")
_HEADER_NAME = re.compile(r"^[!#$%&'*+.^_`|~0-9a-z-]+$")
_MAX_SECRET_BYTES = 8192
_FORBIDDEN_HEADER_NAMES = frozenset(
    {
        "accept-encoding",
        "connection",
        "content-length",
        "cookie",
        "forwarded",
        "host",
        "proxy-authenticate",
        "proxy-authorization",
        "set-cookie",
        "te",
        "trailer",
        "transfer-encoding",
        "upgrade",
        "via",
        "x-forwarded-for",
        "x-forwarded-host",
        "x-forwarded-proto",
    }
)


def _require_utc(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValueError(f"{field_name} must be timezone-aware UTC")


def _canonical_origin(value: str) -> str:
    if not value or value != value.strip():
        raise ValueError("credential_origin must not be blank or padded")
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as exc:
        raise ValueError("credential_origin is invalid") from exc
    if parsed.scheme != "https":
        raise ValueError("credential_origin must use https")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("credential_origin cannot contain userinfo")
    if parsed.hostname is None:
        raise ValueError("credential_origin requires a hostname")
    try:
        parsed.hostname.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError("credential_origin hostname must be ASCII") from exc
    host = parsed.hostname.lower()
    if "*" in host:
        raise ValueError("credential_origin wildcards are forbidden")
    if port not in (None, 443):
        raise ValueError("credential_origin port must be 443")
    if parsed.path not in ("", "/") or parsed.query or parsed.fragment:
        raise ValueError("credential_origin cannot contain path, query or fragment")
    rendered_host = f"[{host}]" if ":" in host else host
    return f"https://{rendered_host}"


class ProviderHttpAuthScheme(StrEnum):
    BEARER_AUTHORIZATION = "BEARER_AUTHORIZATION"
    HEADER_TOKEN = "HEADER_TOKEN"


@dataclass(frozen=True, slots=True)
class ProviderHttpAuthProfile:
    adapter_code: str
    scheme: ProviderHttpAuthScheme
    credential_origin: str
    header_name: str
    max_secret_bytes: int
    auth_evidence_ref: str

    def __post_init__(self) -> None:
        require_versioned_adapter_code(self.adapter_code)
        if self.credential_origin != _canonical_origin(self.credential_origin):
            raise ValueError("credential_origin must be canonical")
        if self.header_name != self.header_name.strip().lower():
            raise ValueError("header_name must be exact lowercase")
        if _HEADER_NAME.fullmatch(self.header_name) is None:
            raise ValueError("header_name is invalid")
        if self.header_name in _FORBIDDEN_HEADER_NAMES:
            raise ValueError("header_name is forbidden")
        if self.scheme is ProviderHttpAuthScheme.BEARER_AUTHORIZATION:
            if self.header_name != "authorization":
                raise ValueError("bearer auth requires authorization header")
        elif self.scheme is ProviderHttpAuthScheme.HEADER_TOKEN:
            if self.header_name == "authorization":
                raise ValueError("header token cannot use authorization header")
        else:
            raise ValueError("unsupported provider HTTP auth scheme")
        if not 1 <= self.max_secret_bytes <= _MAX_SECRET_BYTES:
            raise ValueError("max_secret_bytes is outside the supported range")
        if _EVIDENCE_REFERENCE.fullmatch(self.auth_evidence_ref) is None:
            raise ValueError("auth_evidence_ref must be an opaque evidence reference")

    @property
    def immutable_configuration(self) -> tuple[object, ...]:
        return (
            self.adapter_code,
            self.scheme,
            self.credential_origin,
            self.header_name,
            self.max_secret_bytes,
            self.auth_evidence_ref,
        )


class ProviderHttpAuthRegistry(Protocol):
    def get(self, adapter_code: str) -> ProviderHttpAuthProfile: ...


class InMemoryProviderHttpAuthRegistry:
    def __init__(self, profiles: tuple[ProviderHttpAuthProfile, ...] = ()) -> None:
        entries: dict[str, ProviderHttpAuthProfile] = {}
        for profile in profiles:
            existing = entries.get(profile.adapter_code)
            if existing is not None:
                if existing.immutable_configuration != profile.immutable_configuration:
                    raise ValueError("conflicting provider HTTP auth profile")
                raise ValueError("duplicate provider HTTP auth profile")
            entries[profile.adapter_code] = profile
        self._profiles = MappingProxyType(entries)

    def get(self, adapter_code: str) -> ProviderHttpAuthProfile:
        require_versioned_adapter_code(adapter_code)
        try:
            return self._profiles[adapter_code]
        except KeyError as exc:
            raise KeyError(adapter_code) from exc


class OwnedSensitiveHttpHeaders:
    __slots__ = ("_entries", "_closed")
    __hash__ = None

    def __init__(self, entries: tuple[tuple[str, bytearray], ...]) -> None:
        if not entries:
            raise ValueError("sensitive headers must not be empty")
        names = tuple(name for name, _ in entries)
        if names != tuple(sorted(set(names))):
            raise ValueError("sensitive header names must be unique and sorted")
        if any(not value for _, value in entries):
            raise ValueError("sensitive header values must not be empty")
        self._entries = tuple((name, bytearray(value)) for name, value in entries)
        self._closed = False

    @property
    def closed(self) -> bool:
        return self._closed

    def use_headers(
        self,
        callback: Callable[[tuple[tuple[str, memoryview], ...]], T],
    ) -> T:
        if self._closed:
            raise RuntimeError("SENSITIVE_HTTP_HEADERS_CLOSED")
        views = tuple(
            (name, memoryview(value).toreadonly()) for name, value in self._entries
        )
        try:
            return callback(views)
        finally:
            for _, view in views:
                view.release()

    def close(self) -> None:
        if self._closed:
            return
        for _, value in self._entries:
            for index in range(len(value)):
                value[index] = 0
        self._closed = True

    def __enter__(self) -> OwnedSensitiveHttpHeaders:
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        del exc_type, exc, traceback
        self.close()

    def __repr__(self) -> str:
        state = "CLOSED" if self._closed else "ACTIVE"
        return f"<OwnedSensitiveHttpHeaders REDACTED state={state}>"

    def __eq__(self, other: object) -> bool:
        del other
        raise TypeError("sensitive HTTP header comparison is forbidden")

    def __reduce_ex__(self, protocol: int):
        del protocol
        raise TypeError("sensitive HTTP header serialization is forbidden")


def _build_sensitive_headers(
    profile: ProviderHttpAuthProfile,
    secret: memoryview,
) -> OwnedSensitiveHttpHeaders:
    if not secret or len(secret) > profile.max_secret_bytes:
        raise FinalProviderHttpError("PROVIDER_HTTP_AUTH_SECRET_INVALID")
    for item in secret:
        if not 0x21 <= item <= 0x7E:
            raise FinalProviderHttpError("PROVIDER_HTTP_AUTH_SECRET_INVALID")
    value = bytearray()
    if profile.scheme is ProviderHttpAuthScheme.BEARER_AUTHORIZATION:
        value.extend(b"Bearer ")
    value.extend(secret)
    return OwnedSensitiveHttpHeaders(((profile.header_name, value),))


class SecureProviderHttpExecutor:
    def __init__(
        self,
        *,
        auth_registry: ProviderHttpAuthRegistry,
        transport: ControlledProviderHttpTransport,
    ) -> None:
        self._auth_registry = auth_registry
        self._transport = transport

    def execute(
        self,
        request: OutboundHttpRequest,
        *,
        secret: SecretAccess,
        at: datetime,
    ) -> ProviderHttpResponse:
        _require_utc(at, "at")
        try:
            profile = self._auth_registry.get(request.adapter_code)
        except KeyError as exc:
            raise FinalProviderHttpError(
                "PROVIDER_HTTP_AUTH_PROFILE_NOT_REGISTERED"
            ) from exc

        def use_secret(secret_view: memoryview) -> ProviderHttpResponse:
            envelope = _build_sensitive_headers(profile, secret_view)
            try:
                binding = ProviderHttpCredentialBinding(
                    credential_origin=profile.credential_origin,
                    headers=envelope,
                )
                return self._transport.execute(request, credential=binding)
            finally:
                envelope.close()

        try:
            return secret.use_bytes(use_secret, at=at)
        except ProviderHttpError:
            raise
        except RuntimeError as exc:
            raise FinalProviderHttpError(
                "PROVIDER_HTTP_AUTH_SECRET_UNAVAILABLE"
            ) from exc
        except Exception as exc:
            raise FinalProviderHttpError(
                "PROVIDER_HTTP_AUTH_EXECUTION_INVALID"
            ) from exc


__all__ = [
    "InMemoryProviderHttpAuthRegistry",
    "OwnedSensitiveHttpHeaders",
    "ProviderHttpAuthProfile",
    "ProviderHttpAuthRegistry",
    "ProviderHttpAuthScheme",
    "SecureProviderHttpExecutor",
    "SensitiveHttpHeaderAccess",
]
