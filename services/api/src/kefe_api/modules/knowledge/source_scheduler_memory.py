from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from threading import RLock
from uuid import UUID, uuid4

from kefe_api.modules.knowledge.source_scheduler import (
    SourceAcquisitionDispatch,
    SourceAcquisitionDispatchClaim,
    SourceAcquisitionDispatchState,
    SourceAcquisitionSchedule,
    SourceAcquisitionScheduleState,
)


class InMemorySourceAcquisitionSchedulerRepository:
    def __init__(self) -> None:
        self._lock = RLock()
        self._schedules: dict[UUID, SourceAcquisitionSchedule] = {}
        self._schedule_keys: dict[str, UUID] = {}
        self._dispatches: dict[UUID, SourceAcquisitionDispatch] = {}
        self._occurrences: dict[tuple[UUID, datetime], UUID] = {}

    def create_or_get_schedule(
        self,
        schedule: SourceAcquisitionSchedule,
    ) -> SourceAcquisitionSchedule:
        with self._lock:
            existing_id = self._schedule_keys.get(schedule.schedule_key)
            if existing_id is not None:
                return deepcopy(self._schedules[existing_id])
            if schedule.id in self._schedules:
                raise ValueError("source acquisition schedule already exists")
            self._schedules[schedule.id] = deepcopy(schedule)
            self._schedule_keys[schedule.schedule_key] = schedule.id
            return deepcopy(schedule)

    def get_schedule(
        self,
        schedule_id: UUID,
    ) -> SourceAcquisitionSchedule | None:
        with self._lock:
            schedule = self._schedules.get(schedule_id)
            return deepcopy(schedule) if schedule else None

    def update_schedule_lifecycle(
        self,
        schedule: SourceAcquisitionSchedule,
    ) -> None:
        with self._lock:
            current = self._schedules.get(schedule.id)
            if current is None:
                raise KeyError(schedule.id)
            if self._immutable_signature(current) != self._immutable_signature(schedule):
                raise ValueError("source acquisition schedule configuration is immutable")
            if current.next_due_at != schedule.next_due_at:
                raise ValueError("lifecycle update cannot change next_due_at")
            self._schedules[schedule.id] = deepcopy(schedule)

    def plan_due_once(
        self,
        *,
        at: datetime,
    ) -> SourceAcquisitionDispatch | None:
        with self._lock:
            candidates = [
                schedule
                for schedule in self._schedules.values()
                if schedule.state is SourceAcquisitionScheduleState.ACTIVE
                and schedule.next_due_at <= at
            ]
            if not candidates:
                return None
            selected = min(
                candidates,
                key=lambda value: (value.next_due_at, str(value.id)),
            )
            occurrence = (selected.id, selected.next_due_at)
            if occurrence in self._occurrences:
                raise ValueError("source acquisition occurrence already planned")
            dispatch = SourceAcquisitionDispatch(
                id=uuid4(),
                schedule_id=selected.id,
                due_at=selected.next_due_at,
                state=SourceAcquisitionDispatchState.PENDING,
                attempt_count=0,
                created_at=at,
                updated_at=at,
            )
            self._dispatches[dispatch.id] = deepcopy(dispatch)
            self._occurrences[occurrence] = dispatch.id
            self._schedules[selected.id] = deepcopy(
                selected.advance_after_planning(at=at)
            )
            return deepcopy(dispatch)

    def claim_pending_once(
        self,
        *,
        worker_ref: str,
        claimed_at: datetime,
        expires_at: datetime,
    ) -> SourceAcquisitionDispatchClaim | None:
        with self._lock:
            self._recover_stale_locked(at=claimed_at, limit=1000)
            pending = [
                dispatch
                for dispatch in self._dispatches.values()
                if dispatch.state is SourceAcquisitionDispatchState.PENDING
            ]
            if not pending:
                return None
            selected = min(
                pending,
                key=lambda value: (value.due_at, str(value.id)),
            )
            schedule = self._schedules[selected.schedule_id]
            if selected.attempt_count >= schedule.max_dispatch_attempts:
                raise ValueError("pending dispatch exhausted its claim attempts")
            running = selected.claim(
                worker_ref=worker_ref,
                claimed_at=claimed_at,
                expires_at=expires_at,
            )
            self._dispatches[selected.id] = deepcopy(running)
            return SourceAcquisitionDispatchClaim(
                schedule=deepcopy(schedule),
                dispatch=deepcopy(running),
            )

    def heartbeat(
        self,
        *,
        dispatch_id: UUID,
        worker_ref: str,
        heartbeat_at: datetime,
        expires_at: datetime,
    ) -> SourceAcquisitionDispatch:
        with self._lock:
            dispatch = self._dispatches.get(dispatch_id)
            if dispatch is None:
                raise KeyError(dispatch_id)
            updated = dispatch.heartbeat(
                worker_ref=worker_ref,
                at=heartbeat_at,
                expires_at=expires_at,
            )
            self._dispatches[dispatch_id] = deepcopy(updated)
            return deepcopy(updated)

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
    ) -> SourceAcquisitionDispatch:
        with self._lock:
            dispatch = self._dispatches.get(dispatch_id)
            if dispatch is None:
                raise KeyError(dispatch_id)
            completed = dispatch.complete(
                worker_ref=worker_ref,
                at=completed_at,
                target_state=target_state,
                source_artifact_id=source_artifact_id,
                ingestion_run_id=ingestion_run_id,
                error_code=error_code,
            )
            self._dispatches[dispatch_id] = deepcopy(completed)
            return deepcopy(completed)

    def recover_stale(
        self,
        *,
        at: datetime,
        limit: int,
    ) -> tuple[SourceAcquisitionDispatch, ...]:
        with self._lock:
            return tuple(
                deepcopy(item)
                for item in self._recover_stale_locked(at=at, limit=limit)
            )

    def get_dispatch(
        self,
        dispatch_id: UUID,
    ) -> SourceAcquisitionDispatch | None:
        with self._lock:
            dispatch = self._dispatches.get(dispatch_id)
            return deepcopy(dispatch) if dispatch else None

    def list_dispatches(
        self,
        schedule_id: UUID,
    ) -> tuple[SourceAcquisitionDispatch, ...]:
        with self._lock:
            return tuple(
                deepcopy(item)
                for item in sorted(
                    (
                        dispatch
                        for dispatch in self._dispatches.values()
                        if dispatch.schedule_id == schedule_id
                    ),
                    key=lambda value: (value.due_at, str(value.id)),
                )
            )

    def _recover_stale_locked(
        self,
        *,
        at: datetime,
        limit: int,
    ) -> tuple[SourceAcquisitionDispatch, ...]:
        due = sorted(
            (
                dispatch
                for dispatch in self._dispatches.values()
                if dispatch.state is SourceAcquisitionDispatchState.RUNNING
                and dispatch.expires_at is not None
                and dispatch.expires_at <= at
            ),
            key=lambda value: (value.expires_at, str(value.id)),
        )[:limit]
        recovered: list[SourceAcquisitionDispatch] = []
        for dispatch in due:
            schedule = self._schedules[dispatch.schedule_id]
            updated = dispatch.recover_stale(
                at=at,
                max_attempts=schedule.max_dispatch_attempts,
            )
            self._dispatches[dispatch.id] = deepcopy(updated)
            recovered.append(updated)
        return tuple(recovered)

    @staticmethod
    def _immutable_signature(schedule: SourceAcquisitionSchedule) -> tuple[object, ...]:
        return (
            schedule.schedule_key,
            schedule.adapter_code,
            schedule.external_locator,
            schedule.pipeline_code,
            schedule.pipeline_version,
            schedule.configuration_hash,
            schedule.taxonomy_version,
            schedule.methodology_version,
            schedule.locale,
            schedule.jurisdiction_code,
            schedule.interval_seconds,
            schedule.max_dispatch_attempts,
            schedule.created_at,
        )
