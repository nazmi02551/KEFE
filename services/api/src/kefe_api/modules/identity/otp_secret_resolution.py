from __future__ import annotations

import os
import re
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Protocol
from urllib.parse import urlsplit
from uuid import UUID

from pydantic import SecretStr

from kefe_api.core.settings import Settings
from kefe_api.modules.knowledge.provider_control import require_secret_reference
from kefe_api.modules.knowledge.provider_secret_execution import (
    InMemorySecretResolverRegistry,
    SecretLease,
    SecretReferenceResolver,
    SecretResolutionFinalError,
    SecretResolutionRetryableError,
    SecretResolverRegistry,
)
from kefe_api.modules.knowledge.source_identity import require_versioned_adapter_code

OTP_HTTP_ADAPTER_CODE = "otp.http.v1"
OTP_HTTP_SECRET_PERMIT_ID = UUID("9f7d92f8-9058-4f86-a63d-8ce14fac5cc5")
_ENVIRONMENT_NAME = re.compile(r"^[A-Z][A-Z0-9_]{0,127}$")


def _require_utc(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValueError(f"{field_name} must be timezone-aware UTC")


class OtpSecretLeaseResolver(Protocol):
    def resolve(
        self,
        *,
        at: datetime,
        expires_at: datetime,
    ) -> SecretLease: ...


class EnvironmentSecretReferenceResolver:
    """Resolve an opaque envref on demand without retaining its material."""

    scheme = "envref"

    def __init__(
        self,
        reader: Callable[[str], str | None] | None = None,
    ) -> None:
        self._reader = reader or os.environ.get

    def resolve(
        self,
        *,
        secret_ref: str,
        adapter_code: str,
        permit_id: UUID,
        at: datetime,
        expires_at: datetime,
    ) -> SecretLease:
        del permit_id
        require_secret_reference(secret_ref)
        require_versioned_adapter_code(adapter_code)
        _require_utc(at, "at")
        _require_utc(expires_at, "expires_at")
        if expires_at <= at:
            raise SecretResolutionFinalError()

        parsed = urlsplit(secret_ref)
        if (
            parsed.scheme.lower() != self.scheme
            or parsed.username is not None
            or parsed.password is not None
            or parsed.port is not None
            or parsed.path not in ("", "/")
            or parsed.query
            or parsed.fragment
            or _ENVIRONMENT_NAME.fullmatch(parsed.hostname or "") is None
        ):
            raise SecretResolutionFinalError()
        variable_name = parsed.hostname or ""
        try:
            value = self._reader(variable_name)
        except (OSError, TimeoutError) as exc:
            raise SecretResolutionRetryableError() from exc
        except Exception as exc:
            raise SecretResolutionFinalError() from exc
        if value is None:
            raise SecretResolutionRetryableError()
        if not isinstance(value, str):
            raise SecretResolutionFinalError()
        try:
            material = value.encode("ascii")
        except UnicodeEncodeError as exc:
            raise SecretResolutionFinalError() from exc
        try:
            return SecretLease(material, expires_at=expires_at)
        except ValueError as exc:
            raise SecretResolutionFinalError() from exc

    def __repr__(self) -> str:
        return "EnvironmentSecretReferenceResolver(reader=<redacted>)"


class RegistryBackedOtpSecretLeaseResolver:
    __slots__ = ("_registry", "_secret_ref", "_lease_ttl_seconds")

    def __init__(
        self,
        *,
        registry: SecretResolverRegistry,
        secret_ref: str,
        lease_ttl_seconds: int,
    ) -> None:
        require_secret_reference(secret_ref)
        if not 1 <= lease_ttl_seconds <= 300:
            raise ValueError("OTP secret lease TTL is outside the supported range")
        self._registry = registry
        self._secret_ref = secret_ref
        self._lease_ttl_seconds = lease_ttl_seconds

    def resolve(
        self,
        *,
        at: datetime,
        expires_at: datetime,
    ) -> SecretLease:
        _require_utc(at, "at")
        _require_utc(expires_at, "expires_at")
        lease_expires_at = min(
            expires_at,
            at + timedelta(seconds=self._lease_ttl_seconds),
        )
        if lease_expires_at <= at:
            raise SecretResolutionFinalError()
        try:
            resolver = self._registry.get_for_reference(self._secret_ref)
        except KeyError as exc:
            raise SecretResolutionFinalError() from exc
        return resolver.resolve(
            secret_ref=self._secret_ref,
            adapter_code=OTP_HTTP_ADAPTER_CODE,
            permit_id=OTP_HTTP_SECRET_PERMIT_ID,
            at=at,
            expires_at=lease_expires_at,
        )

    def __repr__(self) -> str:
        return (
            "RegistryBackedOtpSecretLeaseResolver("
            "registry=<redacted>, secret_ref=<redacted>, "
            f"lease_ttl_seconds={self._lease_ttl_seconds})"
        )


class StaticOtpSecretLeaseResolver:
    """Non-production compatibility resolver for direct SecretStr configuration."""

    __slots__ = ("_secret", "_lease_ttl_seconds")

    def __init__(self, secret: SecretStr | str, *, lease_ttl_seconds: int) -> None:
        if not 1 <= lease_ttl_seconds <= 300:
            raise ValueError("OTP secret lease TTL is outside the supported range")
        self._secret = secret if isinstance(secret, SecretStr) else SecretStr(secret)
        self._lease_ttl_seconds = lease_ttl_seconds

    def resolve(
        self,
        *,
        at: datetime,
        expires_at: datetime,
    ) -> SecretLease:
        _require_utc(at, "at")
        _require_utc(expires_at, "expires_at")
        lease_expires_at = min(
            expires_at,
            at + timedelta(seconds=self._lease_ttl_seconds),
        )
        if lease_expires_at <= at:
            raise SecretResolutionFinalError()
        try:
            material = self._secret.get_secret_value().encode("ascii")
        except UnicodeEncodeError as exc:
            raise SecretResolutionFinalError() from exc
        try:
            return SecretLease(material, expires_at=lease_expires_at)
        except ValueError as exc:
            raise SecretResolutionFinalError() from exc

    def __repr__(self) -> str:
        return (
            "StaticOtpSecretLeaseResolver(secret=<redacted>, "
            f"lease_ttl_seconds={self._lease_ttl_seconds})"
        )


def default_otp_secret_resolver_registry() -> SecretResolverRegistry:
    resolver: SecretReferenceResolver = EnvironmentSecretReferenceResolver()
    return InMemorySecretResolverRegistry((resolver,))


def build_otp_secret_lease_resolver(
    settings: Settings,
    *,
    registry: SecretResolverRegistry | None = None,
) -> OtpSecretLeaseResolver:
    production = settings.environment.strip().lower() == "production"
    secret_ref_setting = settings.otp_http_secret_ref
    direct_secret = settings.otp_http_bearer_token

    if production and direct_secret is not None:
        raise RuntimeError(
            "production forbids KEFE_OTP_HTTP_BEARER_TOKEN; "
            "use KEFE_OTP_HTTP_SECRET_REF"
        )
    if secret_ref_setting is not None:
        secret_ref = secret_ref_setting.get_secret_value()
        return RegistryBackedOtpSecretLeaseResolver(
            registry=registry or default_otp_secret_resolver_registry(),
            secret_ref=secret_ref,
            lease_ttl_seconds=settings.otp_http_secret_lease_seconds,
        )
    if direct_secret is not None and not production:
        return StaticOtpSecretLeaseResolver(
            direct_secret,
            lease_ttl_seconds=settings.otp_http_secret_lease_seconds,
        )
    raise RuntimeError(
        "HTTP OTP delivery requires KEFE_OTP_HTTP_SECRET_REF"
        + (
            ""
            if production
            else " or non-production KEFE_OTP_HTTP_BEARER_TOKEN"
        )
    )


__all__ = [
    "EnvironmentSecretReferenceResolver",
    "OTP_HTTP_ADAPTER_CODE",
    "OTP_HTTP_SECRET_PERMIT_ID",
    "OtpSecretLeaseResolver",
    "RegistryBackedOtpSecretLeaseResolver",
    "StaticOtpSecretLeaseResolver",
    "build_otp_secret_lease_resolver",
    "default_otp_secret_resolver_registry",
]
