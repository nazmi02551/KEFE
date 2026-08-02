from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from kefe_api.modules.knowledge.provider_control import (
    ProviderAdmissionResult,
    ProviderCapabilityLifecycle,
    ProviderCapturePermit,
    SourceProviderCapability,
)
from kefe_api.modules.knowledge.provider_execution_context import (
    ProviderPermitExecutionContext,
)


class SourceProviderAdmissionRepository(Protocol):
    def create_or_get(
        self,
        capability: SourceProviderCapability,
    ) -> SourceProviderCapability: ...

    def get(self, adapter_code: str) -> SourceProviderCapability | None: ...

    def get_active_execution_context(
        self,
        *,
        permit_id: UUID,
        adapter_code: str,
        at: datetime,
    ) -> ProviderPermitExecutionContext: ...

    def transition_lifecycle(
        self,
        *,
        adapter_code: str,
        target: ProviderCapabilityLifecycle,
        at: datetime,
    ) -> SourceProviderCapability: ...

    def admit(
        self,
        *,
        adapter_code: str,
        at: datetime,
    ) -> ProviderAdmissionResult: ...

    def complete_success(
        self,
        *,
        permit_id: UUID,
        adapter_code: str,
        at: datetime,
    ) -> ProviderCapturePermit: ...

    def complete_failure(
        self,
        *,
        permit_id: UUID,
        adapter_code: str,
        at: datetime,
        failure_code: str,
    ) -> ProviderCapturePermit: ...
