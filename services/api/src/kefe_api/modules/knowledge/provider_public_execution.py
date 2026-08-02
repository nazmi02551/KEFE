from __future__ import annotations

from datetime import UTC, datetime
from types import MappingProxyType
from typing import Protocol
from uuid import UUID

from kefe_api.modules.knowledge.provider_control import ProviderCredentialMode
from kefe_api.modules.knowledge.provider_execution_context import (
    ProviderPermitContextError,
)
from kefe_api.modules.knowledge.provider_secret_execution import (
    ProviderPermitExecutionContextRepository,
    SecureProviderCaptureExecutor,
)
from kefe_api.modules.knowledge.source_acquisition import (
    CapturedSource,
    FinalSourceCaptureError,
    RetryableSourceCaptureError,
)
from kefe_api.modules.knowledge.source_identity import require_versioned_adapter_code


def _require_utc(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValueError(f"{field_name} must be timezone-aware UTC")


class PublicSourceCaptureAdapter(Protocol):
    @property
    def adapter_code(self) -> str: ...

    def capture(
        self,
        *,
        external_locator: str,
        trace_id: str,
        at: datetime,
    ) -> CapturedSource: ...


class PublicSourceCaptureRegistry(Protocol):
    def get(self, adapter_code: str) -> PublicSourceCaptureAdapter: ...


class InMemoryPublicSourceCaptureRegistry:
    def __init__(
        self,
        adapters: tuple[PublicSourceCaptureAdapter, ...] = (),
    ) -> None:
        entries: dict[str, PublicSourceCaptureAdapter] = {}
        for adapter in adapters:
            require_versioned_adapter_code(adapter.adapter_code)
            if adapter.adapter_code in entries:
                raise ValueError("duplicate public source capture adapter code")
            entries[adapter.adapter_code] = adapter
        self._adapters = MappingProxyType(entries)

    def get(self, adapter_code: str) -> PublicSourceCaptureAdapter:
        require_versioned_adapter_code(adapter_code)
        try:
            return self._adapters[adapter_code]
        except KeyError as exc:
            raise KeyError("SOURCE_PUBLIC_ADAPTER_NOT_REGISTERED") from exc


class PermitBoundPublicCaptureExecutor:
    def __init__(
        self,
        *,
        contexts: ProviderPermitExecutionContextRepository,
        adapters: PublicSourceCaptureRegistry,
    ) -> None:
        self._contexts = contexts
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

        if context.credential_mode is not ProviderCredentialMode.PUBLIC:
            raise FinalSourceCaptureError(
                "SOURCE_PROVIDER_CREDENTIAL_MODE_MISMATCH"
            )
        if context.secret_ref is not None:
            raise FinalSourceCaptureError(
                "SOURCE_PROVIDER_PERMIT_CONTEXT_INVALID"
            )

        try:
            adapter = self._adapters.get(adapter_code)
        except KeyError as exc:
            raise FinalSourceCaptureError(
                "SOURCE_PUBLIC_ADAPTER_NOT_REGISTERED"
            ) from exc

        try:
            captured = adapter.capture(
                external_locator=external_locator,
                trace_id=trace_id,
                at=at,
            )
        except (RetryableSourceCaptureError, FinalSourceCaptureError):
            raise
        except Exception as exc:
            raise FinalSourceCaptureError(
                "SOURCE_PUBLIC_CAPTURE_UNEXPECTED"
            ) from exc
        if type(captured) is not CapturedSource:
            raise FinalSourceCaptureError(
                "SOURCE_PUBLIC_CAPTURE_CONTRACT_INVALID"
            )
        return captured


class CredentialModeRoutingProviderCaptureExecutor:
    def __init__(
        self,
        *,
        contexts: ProviderPermitExecutionContextRepository,
        public_executor: PermitBoundPublicCaptureExecutor,
        credentialed_executor: SecureProviderCaptureExecutor,
    ) -> None:
        self._contexts = contexts
        self._public_executor = public_executor
        self._credentialed_executor = credentialed_executor

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

        if context.credential_mode is ProviderCredentialMode.PUBLIC:
            return self._public_executor.capture(
                adapter_code=adapter_code,
                permit_id=permit_id,
                external_locator=external_locator,
                trace_id=trace_id,
                at=at,
            )
        if context.credential_mode is ProviderCredentialMode.SECRET_REF:
            return self._credentialed_executor.capture(
                adapter_code=adapter_code,
                permit_id=permit_id,
                external_locator=external_locator,
                trace_id=trace_id,
                at=at,
            )
        raise FinalSourceCaptureError(
            "SOURCE_PROVIDER_CREDENTIAL_MODE_MISMATCH"
        )


__all__ = [
    "CredentialModeRoutingProviderCaptureExecutor",
    "InMemoryPublicSourceCaptureRegistry",
    "PermitBoundPublicCaptureExecutor",
    "PublicSourceCaptureAdapter",
    "PublicSourceCaptureRegistry",
]
