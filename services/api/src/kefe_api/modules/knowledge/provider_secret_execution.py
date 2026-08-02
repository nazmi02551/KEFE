from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from types import MappingProxyType
from typing import Protocol, TypeVar
from urllib.parse import urlsplit
from uuid import UUID

from kefe_api.modules.knowledge.provider_control import require_secret_reference
from kefe_api.modules.knowledge.provider_execution_context import (
    ProviderPermitContextError,
    ProviderPermitExecutionContext,
)
from kefe_api.modules.knowledge.source_acquisition import (
    CapturedSource,
    FinalSourceCaptureError,
    RetryableSourceCaptureError,
)
from kefe_api.modules.knowledge.source_identity import require_versioned_adapter_code

T = TypeVar("T")


def _require_utc(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValueError(f"{field_name} must be timezone-aware UTC")


class ProviderPermitExecutionContextRepository(Protocol):
    def get_active_execution_context(
        self,
        *,
        permit_id: UUID,
        adapter_code: str,
        at: datetime,
    ) -> ProviderPermitExecutionContext: ...


class SecretAccess(Protocol):
    def use_bytes(
        self,
        callback: Callable[[memoryview], T],
        *,
        at: datetime,
    ) -> T: ...


class SecretLease:
    __slots__ = ("_material", "_expires_at", "_closed")
    __hash__ = None

    def __init__(self, material: bytes | bytearray, *, expires_at: datetime) -> None:
        _require_utc(expires_at, "expires_at")
        if not material:
            raise ValueError("secret material must not be empty")
        self._material = bytearray(material)
        self._expires_at = expires_at
        self._closed = False

    @property
    def expires_at(self) -> datetime:
        return self._expires_at

    @property
    def closed(self) -> bool:
        return self._closed

    def use_bytes(
        self,
        callback: Callable[[memoryview], T],
        *,
        at: datetime,
    ) -> T:
        _require_utc(at, "at")
        if self._closed:
            raise RuntimeError("SECRET_LEASE_CLOSED")
        if at >= self._expires_at:
            raise RuntimeError("SECRET_LEASE_EXPIRED")
        view = memoryview(self._material).toreadonly()
        try:
            return callback(view)
        finally:
            view.release()

    def close(self) -> None:
        if self._closed:
            return
        for index in range(len(self._material)):
            self._material[index] = 0
        self._closed = True

    def __enter__(self) -> SecretLease:
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        del exc_type, exc, traceback
        self.close()

    def __repr__(self) -> str:
        state = "CLOSED" if self._closed else "ACTIVE"
        return f"<SecretLease REDACTED state={state}>"

    def __eq__(self, other: object) -> bool:
        del other
        raise TypeError("SecretLease comparison is forbidden")

    def __reduce_ex__(self, protocol: int):
        del protocol
        raise TypeError("SecretLease serialization is forbidden")


class SecretResolutionRetryableError(Exception):
    def __str__(self) -> str:
        return "SOURCE_SECRET_RESOLUTION_RETRYABLE"


class SecretResolutionFinalError(Exception):
    def __str__(self) -> str:
        return "SOURCE_SECRET_RESOLUTION_FINAL"


class SecretReferenceResolver(Protocol):
    @property
    def scheme(self) -> str: ...

    def resolve(
        self,
        *,
        secret_ref: str,
        adapter_code: str,
        permit_id: UUID,
        at: datetime,
        expires_at: datetime,
    ) -> SecretLease: ...


class SecretResolverRegistry(Protocol):
    def get_for_reference(self, secret_ref: str) -> SecretReferenceResolver: ...


class InMemorySecretResolverRegistry:
    def __init__(self, resolvers: tuple[SecretReferenceResolver, ...] = ()) -> None:
        entries: dict[str, SecretReferenceResolver] = {}
        for resolver in resolvers:
            scheme = resolver.scheme.strip().lower()
            if not scheme or ":" in scheme or "/" in scheme:
                raise ValueError("invalid secret resolver scheme")
            if scheme in entries:
                raise ValueError("duplicate secret resolver scheme")
            entries[scheme] = resolver
        self._resolvers = MappingProxyType(entries)

    def get_for_reference(self, secret_ref: str) -> SecretReferenceResolver:
        require_secret_reference(secret_ref)
        scheme = urlsplit(secret_ref).scheme.lower()
        try:
            return self._resolvers[scheme]
        except KeyError as exc:
            raise KeyError("SOURCE_SECRET_RESOLVER_NOT_REGISTERED") from exc


class CredentialAwareSourceCaptureAdapter(Protocol):
    @property
    def adapter_code(self) -> str: ...

    def capture(
        self,
        *,
        external_locator: str,
        trace_id: str,
        secret: SecretAccess,
        at: datetime,
    ) -> CapturedSource: ...


class CredentialAwareSourceCaptureRegistry(Protocol):
    def get(self, adapter_code: str) -> CredentialAwareSourceCaptureAdapter: ...


class InMemoryCredentialAwareSourceCaptureRegistry:
    def __init__(
        self,
        adapters: tuple[CredentialAwareSourceCaptureAdapter, ...] = (),
    ) -> None:
        entries: dict[str, CredentialAwareSourceCaptureAdapter] = {}
        for adapter in adapters:
            require_versioned_adapter_code(adapter.adapter_code)
            if adapter.adapter_code in entries:
                raise ValueError("duplicate credential-aware adapter code")
            entries[adapter.adapter_code] = adapter
        self._adapters = MappingProxyType(entries)

    def get(self, adapter_code: str) -> CredentialAwareSourceCaptureAdapter:
        require_versioned_adapter_code(adapter_code)
        try:
            return self._adapters[adapter_code]
        except KeyError as exc:
            raise KeyError("SOURCE_CREDENTIAL_ADAPTER_NOT_REGISTERED") from exc


class SecureProviderCaptureExecutor:
    def __init__(
        self,
        *,
        contexts: ProviderPermitExecutionContextRepository,
        resolvers: SecretResolverRegistry,
        adapters: CredentialAwareSourceCaptureRegistry,
    ) -> None:
        self._contexts = contexts
        self._resolvers = resolvers
        self._adapters = adapters

    def capture(
        self,
        *,
        adapter_code: str,
        permit_id: UUID,
        external_locator: str,
        trace_id: str,
        at: datetime,
    ) -> CapturedSource:
        require_versioned_adapter_code(adapter_code)
        _require_utc(at, "at")
        try:
            context = self._contexts.get_active_execution_context(
                permit_id=permit_id,
                adapter_code=adapter_code,
                at=at,
            )
        except ProviderPermitContextError as exc:
            raise FinalSourceCaptureError(exc.code) from exc
        except Exception as exc:
            raise FinalSourceCaptureError(
                "SOURCE_PROVIDER_PERMIT_CONTEXT_INVALID"
            ) from exc

        try:
            resolver = self._resolvers.get_for_reference(context.secret_ref)
        except KeyError as exc:
            raise FinalSourceCaptureError(
                "SOURCE_SECRET_RESOLVER_NOT_REGISTERED"
            ) from exc

        try:
            lease = resolver.resolve(
                secret_ref=context.secret_ref,
                adapter_code=adapter_code,
                permit_id=permit_id,
                at=at,
                expires_at=context.permit_expires_at,
            )
        except SecretResolutionRetryableError as exc:
            raise RetryableSourceCaptureError(
                "SOURCE_SECRET_RESOLUTION_RETRYABLE"
            ) from exc
        except SecretResolutionFinalError as exc:
            raise FinalSourceCaptureError("SOURCE_SECRET_RESOLUTION_FINAL") from exc
        except Exception as exc:
            raise FinalSourceCaptureError(
                "SOURCE_SECRET_RESOLUTION_UNEXPECTED"
            ) from exc

        try:
            try:
                adapter = self._adapters.get(adapter_code)
            except KeyError as exc:
                raise FinalSourceCaptureError(
                    "SOURCE_CREDENTIAL_ADAPTER_NOT_REGISTERED"
                ) from exc
            captured = adapter.capture(
                external_locator=external_locator,
                trace_id=trace_id,
                secret=lease,
                at=at,
            )
            if not isinstance(captured, CapturedSource):
                raise FinalSourceCaptureError("SOURCE_CAPTURE_CONTRACT_INVALID")
            return captured
        finally:
            lease.close()
