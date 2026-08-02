from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum
from time import monotonic_ns
from typing import Protocol
from uuid import UUID, uuid4

from kefe_api.modules.ingestion_orchestration.models import utcnow
from kefe_api.modules.knowledge.source_acquisition import (
    SourceAcquisitionOutcome,
    SourceAcquisitionService,
)
from kefe_api.modules.knowledge.source_scheduler import (
    MAXIMUM_DISPATCH_ATTEMPTS,
    MAXIMUM_DISPATCH_TTL_SECONDS,
    MAXIMUM_INTERVAL_SECONDS,
    MINIMUM_DISPATCH_ATTEMPTS,
    MINIMUM_DISPATCH_TTL_SECONDS,
    MINIMUM_INTERVAL_SECONDS,
    SourceAcquisitionDispatch,
    SourceAcquisitionDispatchClaim,
    SourceAcquisitionDispatchState,
    SourceAcquisitionSchedule,
    SourceAcquisitionScheduleState,
    build_source_schedule_key,
)
from kefe_api.modules.knowledge.source_scheduler_ports import (
    SourceAcquisitionSchedulerRepository,
)

MAXIMUM_STALE_RECOVERY_BATCH = 1000


def _require_text(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} must not be blank")


@dataclass(frozen=True, slots=True)
class SourceDispatchLeaseError(Exception):
    code: str

    def __post_init__(self) -> None:
        _require_text(self.code, "code")


class SourceDispatchExecutionOutcome(StrEnum):
    IDLE = "IDLE"
    SUCCEEDED = "SUCCEEDED"
    RETRYABLE_FAILURE = "RETRYABLE_FAILURE"
    FINAL_FAILURE = "FINAL_FAILURE"
    BLOCKED = "BLOCKED"
    LEASE_LOST = "LEASE_LOST"


@dataclass(frozen=True, slots=True)
class SourceDispatchExecutionResult:
    outcome: SourceDispatchExecutionOutcome
    worker_ref: str
    duration_ms: int
    schedule_id: UUID | None = None
    dispatch_id: UUID | None = None
    due_at: object | None = None
    attempt_count: int = 0
    source_artifact_id: UUID | None = None
    ingestion_run_id: UUID | None = None
    error_code: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.worker_ref, "worker_ref")
        if self.duration_ms < 0:
            raise ValueError("duration_ms must be >= 0")
        if self.attempt_count < 0:
            raise ValueError("attempt_count must be >= 0")
        if self.error_code is not None:
            _require_text(self.error_code, "error_code")

    def as_operational_dict(self) -> dict[str, str | int | None]:
        return {
            "outcome": self.outcome.value,
            "worker_ref": self.worker_ref,
            "schedule_id": str(self.schedule_id) if self.schedule_id else None,
            "dispatch_id": str(self.dispatch_id) if self.dispatch_id else None,
            "due_at": self.due_at.isoformat() if self.due_at else None,
            "attempt_count": self.attempt_count,
            "source_artifact_id": (
                str(self.source_artifact_id) if self.source_artifact_id else None
            ),
            "ingestion_run_id": (
                str(self.ingestion_run_id) if self.ingestion_run_id else None
            ),
            "duration_ms": self.duration_ms,
            "error_code": self.error_code,
        }


class SourceDispatchObserver(Protocol):
    def record(self, result: SourceDispatchExecutionResult) -> None: ...


class NoOpSourceDispatchObserver:
    def record(self, result: SourceDispatchExecutionResult) -> None:
        del result


class InMemorySourceDispatchObserver:
    def __init__(self) -> None:
        self.results: list[SourceDispatchExecutionResult] = []

    def record(self, result: SourceDispatchExecutionResult) -> None:
        self.results.append(result)


class SourceAcquisitionSchedulerService:
    def __init__(
        self,
        *,
        repository: SourceAcquisitionSchedulerRepository,
        acquisition: SourceAcquisitionService,
        observer: SourceDispatchObserver,
        clock=utcnow,
        monotonic_clock=monotonic_ns,
    ) -> None:
        self._repository = repository
        self._acquisition = acquisition
        self._observer = observer
        self._clock = clock
        self._monotonic_clock = monotonic_clock

    def create_schedule(
        self,
        *,
        adapter_code: str,
        external_locator: str,
        pipeline_code: str,
        pipeline_version: str,
        configuration_hash: str,
        first_due_at,
        interval_seconds: int,
        max_dispatch_attempts: int,
        taxonomy_version: str | None = None,
        methodology_version: str | None = None,
        locale: str | None = None,
        jurisdiction_code: str | None = None,
        now=None,
    ) -> SourceAcquisitionSchedule:
        if not MINIMUM_INTERVAL_SECONDS <= interval_seconds <= MAXIMUM_INTERVAL_SECONDS:
            raise ValueError("interval_seconds is outside the supported range")
        if not (
            MINIMUM_DISPATCH_ATTEMPTS
            <= max_dispatch_attempts
            <= MAXIMUM_DISPATCH_ATTEMPTS
        ):
            raise ValueError("max_dispatch_attempts is outside the supported range")
        created_at = now or self._clock()
        schedule = SourceAcquisitionSchedule(
            id=uuid4(),
            schedule_key=build_source_schedule_key(
                adapter_code=adapter_code,
                external_locator=external_locator,
                pipeline_code=pipeline_code,
                pipeline_version=pipeline_version,
                configuration_hash=configuration_hash,
                first_due_at=first_due_at,
                interval_seconds=interval_seconds,
                max_dispatch_attempts=max_dispatch_attempts,
                taxonomy_version=taxonomy_version,
                methodology_version=methodology_version,
                locale=locale,
                jurisdiction_code=jurisdiction_code,
            ),
            adapter_code=adapter_code,
            external_locator=external_locator,
            pipeline_code=pipeline_code,
            pipeline_version=pipeline_version,
            configuration_hash=configuration_hash,
            taxonomy_version=taxonomy_version,
            methodology_version=methodology_version,
            locale=locale,
            jurisdiction_code=jurisdiction_code,
            interval_seconds=interval_seconds,
            max_dispatch_attempts=max_dispatch_attempts,
            state=SourceAcquisitionScheduleState.ACTIVE,
            next_due_at=first_due_at,
            created_at=created_at,
            updated_at=created_at,
        )
        return self._repository.create_or_get_schedule(schedule)

    def pause(self, schedule_id: UUID, *, now=None) -> SourceAcquisitionSchedule:
        return self._transition(
            schedule_id,
            SourceAcquisitionScheduleState.PAUSED,
            now=now,
        )

    def resume(self, schedule_id: UUID, *, now=None) -> SourceAcquisitionSchedule:
        return self._transition(
            schedule_id,
            SourceAcquisitionScheduleState.ACTIVE,
            now=now,
        )

    def retire(self, schedule_id: UUID, *, now=None) -> SourceAcquisitionSchedule:
        return self._transition(
            schedule_id,
            SourceAcquisitionScheduleState.RETIRED,
            now=now,
        )

    def plan_due_once(self, *, now=None) -> SourceAcquisitionDispatch | None:
        return self._repository.plan_due_once(at=now or self._clock())

    def recover_stale(
        self,
        *,
        limit: int = 100,
        now=None,
    ) -> tuple[SourceAcquisitionDispatch, ...]:
        if limit < 1 or limit > MAXIMUM_STALE_RECOVERY_BATCH:
            raise ValueError(
                f"recovery limit must be between 1 and {MAXIMUM_STALE_RECOVERY_BATCH}"
            )
        return self._repository.recover_stale(
            at=now or self._clock(),
            limit=limit,
        )

    def execute_pending_once(
        self,
        *,
        worker_ref: str,
        ttl_seconds: int,
        trace_id: str | None = None,
        now=None,
    ) -> SourceDispatchExecutionResult:
        _require_text(worker_ref, "worker_ref")
        if not (
            MINIMUM_DISPATCH_TTL_SECONDS
            <= ttl_seconds
            <= MAXIMUM_DISPATCH_TTL_SECONDS
        ):
            raise ValueError("dispatch TTL is outside the supported range")
        started_ns = self._monotonic_clock()
        claimed_at = now or self._clock()
        claim = self._repository.claim_pending_once(
            worker_ref=worker_ref,
            claimed_at=claimed_at,
            expires_at=claimed_at + timedelta(seconds=ttl_seconds),
        )
        if claim is None:
            return self._emit(
                self._result(
                    started_ns=started_ns,
                    outcome=SourceDispatchExecutionOutcome.IDLE,
                    worker_ref=worker_ref,
                )
            )

        try:
            self._heartbeat(claim, worker_ref=worker_ref, ttl_seconds=ttl_seconds)
            acquisition = self._acquisition.acquire(
                claim.schedule.acquisition_command(),
                trace_id=trace_id,
                before_artifact_persist=lambda: self._heartbeat(
                    claim,
                    worker_ref=worker_ref,
                    ttl_seconds=ttl_seconds,
                ),
                before_run_admission=lambda: self._heartbeat(
                    claim,
                    worker_ref=worker_ref,
                    ttl_seconds=ttl_seconds,
                ),
            )
            self._heartbeat(claim, worker_ref=worker_ref, ttl_seconds=ttl_seconds)
            target_state, outcome = self._map_acquisition_outcome(acquisition.outcome)
            completed = self._complete(
                claim,
                worker_ref=worker_ref,
                target_state=target_state,
                source_artifact_id=acquisition.source_artifact_id,
                ingestion_run_id=acquisition.ingestion_run_id,
                error_code=acquisition.error_code,
            )
            return self._emit(
                self._result_from_dispatch(
                    started_ns=started_ns,
                    outcome=outcome,
                    worker_ref=worker_ref,
                    dispatch=completed,
                )
            )
        except SourceDispatchLeaseError as exc:
            return self._emit(
                self._result_from_claim(
                    started_ns=started_ns,
                    outcome=SourceDispatchExecutionOutcome.LEASE_LOST,
                    worker_ref=worker_ref,
                    claim=claim,
                    error_code=exc.code,
                )
            )
        except Exception:
            try:
                self._heartbeat(claim, worker_ref=worker_ref, ttl_seconds=ttl_seconds)
                completed = self._complete(
                    claim,
                    worker_ref=worker_ref,
                    target_state=SourceAcquisitionDispatchState.FINAL_FAILURE,
                    error_code="SOURCE_DISPATCH_EXECUTION_UNEXPECTED",
                )
                return self._emit(
                    self._result_from_dispatch(
                        started_ns=started_ns,
                        outcome=SourceDispatchExecutionOutcome.FINAL_FAILURE,
                        worker_ref=worker_ref,
                        dispatch=completed,
                    )
                )
            except SourceDispatchLeaseError as exc:
                return self._emit(
                    self._result_from_claim(
                        started_ns=started_ns,
                        outcome=SourceDispatchExecutionOutcome.LEASE_LOST,
                        worker_ref=worker_ref,
                        claim=claim,
                        error_code=exc.code,
                    )
                )

    def _transition(
        self,
        schedule_id: UUID,
        target: SourceAcquisitionScheduleState,
        *,
        now=None,
    ) -> SourceAcquisitionSchedule:
        schedule = self._repository.get_schedule(schedule_id)
        if schedule is None:
            raise KeyError(schedule_id)
        updated = schedule.transition(target, at=now or self._clock())
        self._repository.update_schedule_lifecycle(updated)
        return self._repository.get_schedule(schedule_id) or updated

    def _heartbeat(
        self,
        claim: SourceAcquisitionDispatchClaim,
        *,
        worker_ref: str,
        ttl_seconds: int,
    ) -> SourceAcquisitionDispatch:
        at = self._clock()
        try:
            return self._repository.heartbeat(
                dispatch_id=claim.dispatch.id,
                worker_ref=worker_ref,
                heartbeat_at=at,
                expires_at=at + timedelta(seconds=ttl_seconds),
            )
        except KeyError as exc:
            raise SourceDispatchLeaseError("SOURCE_DISPATCH_NOT_FOUND") from exc
        except ValueError as exc:
            raise SourceDispatchLeaseError("SOURCE_DISPATCH_LEASE_NOT_ACTIVE") from exc

    def _complete(
        self,
        claim: SourceAcquisitionDispatchClaim,
        *,
        worker_ref: str,
        target_state: SourceAcquisitionDispatchState,
        source_artifact_id: UUID | None = None,
        ingestion_run_id: UUID | None = None,
        error_code: str | None = None,
    ) -> SourceAcquisitionDispatch:
        try:
            return self._repository.complete(
                dispatch_id=claim.dispatch.id,
                worker_ref=worker_ref,
                completed_at=self._clock(),
                target_state=target_state,
                source_artifact_id=source_artifact_id,
                ingestion_run_id=ingestion_run_id,
                error_code=error_code,
            )
        except KeyError as exc:
            raise SourceDispatchLeaseError("SOURCE_DISPATCH_NOT_FOUND") from exc
        except ValueError as exc:
            raise SourceDispatchLeaseError("SOURCE_DISPATCH_LEASE_NOT_ACTIVE") from exc

    @staticmethod
    def _map_acquisition_outcome(outcome: SourceAcquisitionOutcome):
        mapping = {
            SourceAcquisitionOutcome.ADMITTED: (
                SourceAcquisitionDispatchState.SUCCEEDED,
                SourceDispatchExecutionOutcome.SUCCEEDED,
            ),
            SourceAcquisitionOutcome.RETRYABLE_FAILURE: (
                SourceAcquisitionDispatchState.RETRYABLE_FAILURE,
                SourceDispatchExecutionOutcome.RETRYABLE_FAILURE,
            ),
            SourceAcquisitionOutcome.FINAL_FAILURE: (
                SourceAcquisitionDispatchState.FINAL_FAILURE,
                SourceDispatchExecutionOutcome.FINAL_FAILURE,
            ),
            SourceAcquisitionOutcome.BLOCKED: (
                SourceAcquisitionDispatchState.BLOCKED,
                SourceDispatchExecutionOutcome.BLOCKED,
            ),
        }
        return mapping[outcome]

    def _result(
        self,
        *,
        started_ns: int,
        outcome: SourceDispatchExecutionOutcome,
        worker_ref: str,
        schedule_id: UUID | None = None,
        dispatch_id: UUID | None = None,
        due_at=None,
        attempt_count: int = 0,
        source_artifact_id: UUID | None = None,
        ingestion_run_id: UUID | None = None,
        error_code: str | None = None,
    ) -> SourceDispatchExecutionResult:
        elapsed_ns = max(0, self._monotonic_clock() - started_ns)
        return SourceDispatchExecutionResult(
            outcome=outcome,
            worker_ref=worker_ref,
            schedule_id=schedule_id,
            dispatch_id=dispatch_id,
            due_at=due_at,
            attempt_count=attempt_count,
            source_artifact_id=source_artifact_id,
            ingestion_run_id=ingestion_run_id,
            duration_ms=elapsed_ns // 1_000_000,
            error_code=error_code,
        )

    def _result_from_claim(
        self,
        *,
        started_ns: int,
        outcome: SourceDispatchExecutionOutcome,
        worker_ref: str,
        claim: SourceAcquisitionDispatchClaim,
        error_code: str,
    ) -> SourceDispatchExecutionResult:
        return self._result(
            started_ns=started_ns,
            outcome=outcome,
            worker_ref=worker_ref,
            schedule_id=claim.schedule.id,
            dispatch_id=claim.dispatch.id,
            due_at=claim.dispatch.due_at,
            attempt_count=claim.dispatch.attempt_count,
            error_code=error_code,
        )

    def _result_from_dispatch(
        self,
        *,
        started_ns: int,
        outcome: SourceDispatchExecutionOutcome,
        worker_ref: str,
        dispatch: SourceAcquisitionDispatch,
    ) -> SourceDispatchExecutionResult:
        return self._result(
            started_ns=started_ns,
            outcome=outcome,
            worker_ref=worker_ref,
            schedule_id=dispatch.schedule_id,
            dispatch_id=dispatch.id,
            due_at=dispatch.due_at,
            attempt_count=dispatch.attempt_count,
            source_artifact_id=dispatch.source_artifact_id,
            ingestion_run_id=dispatch.ingestion_run_id,
            error_code=dispatch.error_code,
        )

    def _emit(
        self,
        result: SourceDispatchExecutionResult,
    ) -> SourceDispatchExecutionResult:
        try:
            self._observer.record(result)
        except Exception:
            pass
        return result
