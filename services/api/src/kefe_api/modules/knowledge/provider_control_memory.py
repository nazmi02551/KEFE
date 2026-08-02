from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta
from threading import RLock
from uuid import UUID

from kefe_api.modules.knowledge.provider_control import (
    ProviderAdmissionOutcome,
    ProviderAdmissionResult,
    ProviderCapabilityLifecycle,
    ProviderCapturePermit,
    ProviderCapturePermitState,
    ProviderCircuitState,
    SourceProviderCapability,
)
from kefe_api.modules.knowledge.provider_execution_context import (
    ProviderPermitContextError,
    ProviderPermitExecutionContext,
)
from kefe_api.modules.knowledge.source_acquisition import (
    require_versioned_adapter_code,
)


class InMemorySourceProviderAdmissionRepository:
    def __init__(self) -> None:
        self._lock = RLock()
        self._capabilities: dict[str, SourceProviderCapability] = {}
        self._permits: dict[UUID, ProviderCapturePermit] = {}

    def create_or_get(
        self,
        capability: SourceProviderCapability,
    ) -> SourceProviderCapability:
        with self._lock:
            existing = self._capabilities.get(capability.adapter_code)
            if existing is not None:
                if existing.immutable_configuration != capability.immutable_configuration:
                    raise ValueError(
                        "provider capability configuration is immutable"
                    )
                return deepcopy(existing)
            self._capabilities[capability.adapter_code] = deepcopy(capability)
            return deepcopy(capability)

    def get(self, adapter_code: str) -> SourceProviderCapability | None:
        require_versioned_adapter_code(adapter_code)
        with self._lock:
            capability = self._capabilities.get(adapter_code)
            return deepcopy(capability) if capability is not None else None

    def get_active_execution_context(
        self,
        *,
        permit_id: UUID,
        adapter_code: str,
        at: datetime,
    ) -> ProviderPermitExecutionContext:
        require_versioned_adapter_code(adapter_code)
        with self._lock:
            permit = self._permits.get(permit_id)
            capability = self._capabilities.get(adapter_code)
            if permit is None or capability is None:
                raise ProviderPermitContextError()
            try:
                permit.require_active(adapter_code=adapter_code, at=at)
            except ValueError as exc:
                raise ProviderPermitContextError() from exc
            if capability.lifecycle_state is not ProviderCapabilityLifecycle.ENABLED:
                raise ProviderPermitContextError()
            return ProviderPermitExecutionContext(
                permit_id=permit.id,
                adapter_code=adapter_code,
                secret_ref=capability.secret_ref,
                permit_expires_at=permit.expires_at,
            )

    def transition_lifecycle(
        self,
        *,
        adapter_code: str,
        target: ProviderCapabilityLifecycle,
        at: datetime,
    ) -> SourceProviderCapability:
        with self._lock:
            capability = self._require_capability(adapter_code)
            updated = capability.transition_lifecycle(target, at=at)
            self._capabilities[adapter_code] = updated
            return deepcopy(updated)

    def admit(
        self,
        *,
        adapter_code: str,
        at: datetime,
    ) -> ProviderAdmissionResult:
        require_versioned_adapter_code(adapter_code)
        with self._lock:
            capability = self._capabilities.get(adapter_code)
            if capability is None:
                return ProviderAdmissionResult(
                    outcome=ProviderAdmissionOutcome.NOT_REGISTERED,
                    adapter_code=adapter_code,
                    permit_id=None,
                    circuit_state=None,
                    retry_after_seconds=None,
                    reason_code="SOURCE_PROVIDER_NOT_REGISTERED",
                )

            capability = self._recover_expired_locked(capability, at=at)
            capability = capability.roll_quota_window(at=at)
            capability = capability.prepare_circuit_for_admission(at=at)
            self._capabilities[adapter_code] = capability

            if capability.lifecycle_state is ProviderCapabilityLifecycle.PAUSED:
                return self._denied(
                    capability,
                    outcome=ProviderAdmissionOutcome.PAUSED,
                    reason_code="SOURCE_PROVIDER_PAUSED",
                )
            if capability.lifecycle_state is ProviderCapabilityLifecycle.RETIRED:
                return self._denied(
                    capability,
                    outcome=ProviderAdmissionOutcome.RETIRED,
                    reason_code="SOURCE_PROVIDER_RETIRED",
                )
            if capability.circuit_state is ProviderCircuitState.OPEN:
                return self._denied(
                    capability,
                    outcome=ProviderAdmissionOutcome.CIRCUIT_OPEN,
                    reason_code="SOURCE_PROVIDER_CIRCUIT_OPEN",
                    retry_after_seconds=capability.retry_after_for_open_circuit(at=at),
                )
            if (
                capability.circuit_state is ProviderCircuitState.HALF_OPEN
                and self._has_active_probe_locked(adapter_code)
            ):
                return self._denied(
                    capability,
                    outcome=ProviderAdmissionOutcome.CIRCUIT_OPEN,
                    reason_code="SOURCE_PROVIDER_HALF_OPEN_PROBE_ACTIVE",
                    retry_after_seconds=capability.permit_ttl_seconds,
                )
            if capability.window_request_count >= capability.quota_limit:
                return self._denied(
                    capability,
                    outcome=ProviderAdmissionOutcome.RATE_LIMITED,
                    reason_code="SOURCE_PROVIDER_RATE_LIMITED",
                    retry_after_seconds=capability.retry_after_for_quota(at=at),
                )

            is_probe = capability.circuit_state is ProviderCircuitState.HALF_OPEN
            permit = ProviderCapturePermit.create(
                adapter_code=adapter_code,
                admitted_at=at,
                expires_at=at + timedelta(seconds=capability.permit_ttl_seconds),
                was_half_open_probe=is_probe,
            )
            updated = capability.count_admission(at=at)
            self._capabilities[adapter_code] = updated
            self._permits[permit.id] = permit
            return ProviderAdmissionResult(
                outcome=ProviderAdmissionOutcome.ADMITTED,
                adapter_code=adapter_code,
                permit_id=permit.id,
                circuit_state=updated.circuit_state,
                retry_after_seconds=None,
                reason_code="SOURCE_PROVIDER_ADMITTED",
            )

    def complete_success(
        self,
        *,
        permit_id: UUID,
        adapter_code: str,
        at: datetime,
    ) -> ProviderCapturePermit:
        with self._lock:
            permit = self._require_permit(permit_id)
            capability = self._require_capability(adapter_code)
            completed = permit.succeed(adapter_code=adapter_code, at=at)
            updated = capability.record_success(
                at=at,
                was_half_open_probe=permit.was_half_open_probe,
            )
            self._permits[permit_id] = completed
            self._capabilities[adapter_code] = updated
            return deepcopy(completed)

    def complete_failure(
        self,
        *,
        permit_id: UUID,
        adapter_code: str,
        at: datetime,
        failure_code: str,
    ) -> ProviderCapturePermit:
        with self._lock:
            permit = self._require_permit(permit_id)
            capability = self._require_capability(adapter_code)
            completed = permit.fail(
                adapter_code=adapter_code,
                at=at,
                failure_code=failure_code,
            )
            updated = capability.record_failure(
                at=at,
                was_half_open_probe=permit.was_half_open_probe,
            )
            self._permits[permit_id] = completed
            self._capabilities[adapter_code] = updated
            return deepcopy(completed)

    def _recover_expired_locked(
        self,
        capability: SourceProviderCapability,
        *,
        at: datetime,
    ) -> SourceProviderCapability:
        expired = sorted(
            (
                permit
                for permit in self._permits.values()
                if permit.adapter_code == capability.adapter_code
                and permit.state is ProviderCapturePermitState.ACTIVE
                and permit.expires_at <= at
            ),
            key=lambda permit: (permit.expires_at, str(permit.id)),
        )
        included_probe = any(permit.was_half_open_probe for permit in expired)
        for permit in expired:
            self._permits[permit.id] = permit.abandon(at=at)
        return capability.after_expired_permits(
            count=len(expired),
            at=at,
            included_half_open_probe=included_probe,
        )

    def _has_active_probe_locked(self, adapter_code: str) -> bool:
        return any(
            permit.adapter_code == adapter_code
            and permit.state is ProviderCapturePermitState.ACTIVE
            and permit.was_half_open_probe
            for permit in self._permits.values()
        )

    def _require_capability(self, adapter_code: str) -> SourceProviderCapability:
        require_versioned_adapter_code(adapter_code)
        try:
            return self._capabilities[adapter_code]
        except KeyError as exc:
            raise KeyError(adapter_code) from exc

    def _require_permit(self, permit_id: UUID) -> ProviderCapturePermit:
        try:
            return self._permits[permit_id]
        except KeyError as exc:
            raise KeyError(permit_id) from exc

    @staticmethod
    def _denied(
        capability: SourceProviderCapability,
        *,
        outcome: ProviderAdmissionOutcome,
        reason_code: str,
        retry_after_seconds: int | None = None,
    ) -> ProviderAdmissionResult:
        return ProviderAdmissionResult(
            outcome=outcome,
            adapter_code=capability.adapter_code,
            permit_id=None,
            circuit_state=capability.circuit_state,
            retry_after_seconds=retry_after_seconds,
            reason_code=reason_code,
        )
