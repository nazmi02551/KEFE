from __future__ import annotations

from datetime import datetime
from uuid import UUID

from kefe_api.modules.ingestion_orchestration.models import utcnow
from kefe_api.modules.knowledge.provider_control import (
    ProviderAdmissionResult,
    ProviderCapabilityLifecycle,
    ProviderCapturePermit,
    SourceProviderCapability,
)
from kefe_api.modules.knowledge.provider_control_ports import (
    SourceProviderAdmissionRepository,
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
        secret_ref: str,
        quota_limit: int,
        quota_window_seconds: int,
        failure_threshold: int,
        circuit_open_seconds: int,
        permit_ttl_seconds: int,
        created_at: datetime | None = None,
    ) -> SourceProviderCapability:
        at = created_at or self._clock()
        return self._repository.create_or_get(
            SourceProviderCapability.create(
                adapter_code=adapter_code,
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
