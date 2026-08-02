from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from kefe_api.modules.knowledge.source_scheduler import (
    SourceAcquisitionDispatch,
    SourceAcquisitionDispatchClaim,
    SourceAcquisitionDispatchState,
    SourceAcquisitionSchedule,
)


class SourceAcquisitionSchedulerRepository(Protocol):
    def create_or_get_schedule(
        self,
        schedule: SourceAcquisitionSchedule,
    ) -> SourceAcquisitionSchedule: ...

    def get_schedule(
        self,
        schedule_id: UUID,
    ) -> SourceAcquisitionSchedule | None: ...

    def update_schedule_lifecycle(
        self,
        schedule: SourceAcquisitionSchedule,
    ) -> None: ...

    def plan_due_once(
        self,
        *,
        at: datetime,
    ) -> SourceAcquisitionDispatch | None: ...

    def claim_pending_once(
        self,
        *,
        worker_ref: str,
        claimed_at: datetime,
        expires_at: datetime,
    ) -> SourceAcquisitionDispatchClaim | None: ...

    def heartbeat(
        self,
        *,
        dispatch_id: UUID,
        worker_ref: str,
        heartbeat_at: datetime,
        expires_at: datetime,
    ) -> SourceAcquisitionDispatch: ...

    def complete(
        self,
        *,
        dispatch_id: UUID,
        worker_ref: str,
        completed_at: datetime,
        target_state: SourceAcquisitionDispatchState,
        source_artifact_id: UUID | None = None,
        ingestion_run_id: UUID | None = None,
        error_code: str | None = None,
    ) -> SourceAcquisitionDispatch: ...

    def recover_stale(
        self,
        *,
        at: datetime,
        limit: int,
    ) -> tuple[SourceAcquisitionDispatch, ...]: ...

    def get_dispatch(
        self,
        dispatch_id: UUID,
    ) -> SourceAcquisitionDispatch | None: ...

    def list_dispatches(
        self,
        schedule_id: UUID,
    ) -> tuple[SourceAcquisitionDispatch, ...]: ...
