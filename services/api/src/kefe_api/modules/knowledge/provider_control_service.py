from __future__ import annotations

from datetime import datetime
from uuid import UUID

from kefe_api.modules.ingestion_orchestration.models import utcnow
from kefe_api.modules.knowledge.provider_control import (
    ProviderAdmissionOutcome,
    ProviderAdmissionResult,
    ProviderCapabilityLifecycle,
    ProviderCapturePermit,
    ProviderCredentialMode,
    SourceProviderCapability,
)
from kefe_api.modules.knowledge.provider_control_ports import (
    SourceProviderAdmissionRepository,
)
from kefe_api.modules.knowledge.source_acquisition import (
    SourceCaptureAdmissionDecision,
)


class SourceProviderAdmissionService:
    def __init__(
        self,
        repository: SourceProviderAdmissionRepository,
        *,
        clock=utcnow,
    ) -> None:
        self._repository = repository
        self._clock = clock

    def register(
        self,
        *,
        adapter_code: str,
        secret_ref: str | None,
        quota_limit: int,
        quota_window_seconds: int,
        failure_threshold: int,
        circuit_open_seconds: int,
        permit_ttl_seconds: int,
        created_at: datetime | None = None,
        credential_mode: ProviderCredentialMode = ProviderCredentialMode.SECRET_REF,
    ) -> SourceProviderCapability:
        at = created_at or self._clock()
        return self._repository.create_or_get(
            SourceProviderCapability.create(
                adapter_code=adapter_code,
                credential_mode=credential_mode,
                secret_ref=secret_ref,
                quota_limit=quota_limit,
                quota_window_seconds=quota_window_seconds,
                failure_threshold=failure_threshold,
                circuit_open_seconds=circuit_open_seconds,
                permit_ttl_seconds=permit_ttl_seconds,
                created_at=at,
            )
        )

    def pause(
        self,
        adapter_code: str,
        *,
        at: datetime | None = None,
    ) -> SourceProviderCapability:
        return self._repository.transition_lifecycle(
            adapter_code=adapter_code,
            target=ProviderCapabilityLifecycle.PAUSED,
            at=at or self._clock(),
        )

    def resume(
        self,
        adapter_code: str,
        *,
        at: datetime | None = None,
    ) -> SourceProviderCapability:
        return self._repository.transition_lifecycle(
            adapter_code=adapter_code,
            target=ProviderCapabilityLifecycle.ENABLED,
            at=at or self._clock(),
        )

    def retire(
        self,
        adapter_code: str,
        *,
        at: datetime | None = None,
    ) -> SourceProviderCapability:
        return self._repository.transition_lifecycle(
            adapter_code=adapter_code,
            target=ProviderCapabilityLifecycle.RETIRED,
            at=at or self._clock(),
        )

    def admit(
        self,
        *,
        adapter_code: str,
        at: datetime | None = None,
    ) -> ProviderAdmissionResult:
        return self._repository.admit(
            adapter_code=adapter_code,
            at=at or self._clock(),
        )

    def admit_capture(
        self,
        *,
        adapter_code: str,
        at: datetime,
    ) -> SourceCaptureAdmissionDecision:
        result = self.admit(adapter_code=adapter_code, at=at)
        retryable = result.outcome in {
            ProviderAdmissionOutcome.PAUSED,
            ProviderAdmissionOutcome.RATE_LIMITED,
            ProviderAdmissionOutcome.CIRCUIT_OPEN,
        }
        return SourceCaptureAdmissionDecision(
            allowed=result.outcome is ProviderAdmissionOutcome.ADMITTED,
            retryable=retryable,
            permit_id=result.permit_id,
            reason_code=result.reason_code,
        )

    def complete_success(
        self,
        *,
        permit_id: UUID,
        adapter_code: str,
        at: datetime | None = None,
    ) -> ProviderCapturePermit:
        return self._repository.complete_success(
            permit_id=permit_id,
            adapter_code=adapter_code,
            at=at or self._clock(),
        )

    def complete_capture_success(
        self,
        *,
        permit_id: UUID,
        adapter_code: str,
        at: datetime,
    ) -> ProviderCapturePermit:
        return self.complete_success(
            permit_id=permit_id,
            adapter_code=adapter_code,
            at=at,
        )

    def complete_failure(
        self,
        *,
        permit_id: UUID,
        adapter_code: str,
        failure_code: str,
        at: datetime | None = None,
    ) -> ProviderCapturePermit:
        return self._repository.complete_failure(
            permit_id=permit_id,
            adapter_code=adapter_code,
            at=at or self._clock(),
            failure_code=failure_code,
        )

    def complete_capture_failure(
        self,
        *,
        permit_id: UUID,
        adapter_code: str,
        failure_code: str,
        at: datetime,
    ) -> ProviderCapturePermit:
        return self.complete_failure(
            permit_id=permit_id,
            adapter_code=adapter_code,
            failure_code=failure_code,
            at=at,
        )
