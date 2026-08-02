from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum
from time import monotonic_ns
from typing import Protocol
from uuid import UUID

from kefe_api.modules.content_supply_cycle.models import (
    ContentSupplyCycle,
    ContentSupplyCycleCommand,
    ContentSupplyCycleCounters,
    ContentSupplyCycleState,
)
from kefe_api.modules.content_supply_cycle.ports import ContentSupplyCycleRepository
from kefe_api.modules.ingestion_orchestration.models import utcnow
from kefe_api.modules.ingestion_orchestration.worker_runtime import (
    IngestionWorkerRunOutcome,
)
from kefe_api.modules.ingestion_orchestration.worker_service import (
    IngestionWorkerRunner,
)
from kefe_api.modules.knowledge.source_scheduler_service import (
    SourceAcquisitionSchedulerService,
    SourceDispatchExecutionOutcome,
)

MAXIMUM_STALE_CYCLE_RECOVERY_BATCH = 1000


def _require_text(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} must not be blank")


@dataclass(frozen=True, slots=True)
class ContentSupplyCycleLeaseError(Exception):
    code: str

    def __post_init__(self) -> None:
        _require_text(self.code, "code")


class ContentSupplyCycleOutcome(StrEnum):
    IDLE = "IDLE"
    SUCCEEDED = "SUCCEEDED"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"
    LEASE_LOST = "LEASE_LOST"


@dataclass(frozen=True, slots=True)
class ContentSupplyCycleResult:
    outcome: ContentSupplyCycleOutcome
    cycle_id: UUID
    worker_ref: str
    plan_hash: str
    planned_count: int
    dispatch_attempted_count: int
    dispatch_succeeded_count: int
    dispatch_non_success_count: int
    ingestion_attempted_count: int
    ingestion_succeeded_count: int
    ingestion_non_success_count: int
    duration_ms: int
    error_code: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.worker_ref, "worker_ref")
        _require_text(self.plan_hash, "plan_hash")
        if self.duration_ms < 0:
            raise ValueError("duration_ms must be non-negative")
        if self.error_code is not None:
            _require_text(self.error_code, "error_code")

    def as_operational_dict(self) -> dict[str, str | int | None]:
        return {
            "outcome": self.outcome.value,
            "cycle_id": str(self.cycle_id),
            "worker_ref": self.worker_ref,
            "plan_hash": self.plan_hash,
            "planned_count": self.planned_count,
            "dispatch_attempted_count": self.dispatch_attempted_count,
            "dispatch_succeeded_count": self.dispatch_succeeded_count,
            "dispatch_non_success_count": self.dispatch_non_success_count,
            "ingestion_attempted_count": self.ingestion_attempted_count,
            "ingestion_succeeded_count": self.ingestion_succeeded_count,
            "ingestion_non_success_count": self.ingestion_non_success_count,
            "duration_ms": self.duration_ms,
            "error_code": self.error_code,
        }


class ContentSupplyCycleObserver(Protocol):
    def record(self, result: ContentSupplyCycleResult) -> None: ...


class NoOpContentSupplyCycleObserver:
    def record(self, result: ContentSupplyCycleResult) -> None:
        del result


class InMemoryContentSupplyCycleObserver:
    def __init__(self) -> None:
        self.results: list[ContentSupplyCycleResult] = []

    def record(self, result: ContentSupplyCycleResult) -> None:
        self.results.append(result)


class ContentSupplyCycleService:
    def __init__(
        self,
        *,
        repository: ContentSupplyCycleRepository,
        scheduler: SourceAcquisitionSchedulerService,
        ingestion_worker: IngestionWorkerRunner,
        observer: ContentSupplyCycleObserver,
        clock=utcnow,
        monotonic_clock=monotonic_ns,
    ) -> None:
        self._repository = repository
        self._scheduler = scheduler
        self._ingestion_worker = ingestion_worker
        self._observer = observer
        self._clock = clock
        self._monotonic_clock = monotonic_clock

    def run_once(self, command: ContentSupplyCycleCommand) -> ContentSupplyCycleResult:
        started_ns = self._monotonic_clock()
        started_at = self._clock()
        self._repository.recover_stale(at=started_at, limit=100)
        cycle = self._repository.create(
            ContentSupplyCycle.start(
                command,
                started_at=started_at,
                expires_at=started_at
                + timedelta(seconds=command.cycle_ttl_seconds),
            )
        )
        counters = ContentSupplyCycleCounters()

        try:
            for _ in range(command.plan_budget):
                self._heartbeat(cycle, command=command, counters=counters)
                planned = self._scheduler.plan_due_once(now=self._clock())
                if planned is None:
                    break
                counters = counters.add_planned()
                cycle = self._heartbeat(
                    cycle,
                    command=command,
                    counters=counters,
                )

            for dispatch_index in range(command.dispatch_budget):
                self._heartbeat(cycle, command=command, counters=counters)
                result = self._scheduler.execute_pending_once(
                    worker_ref=command.worker_ref,
                    ttl_seconds=command.dispatch_ttl_seconds,
                    trace_id=f"cycle:{cycle.id}:dispatch:{dispatch_index + 1}",
                    now=self._clock(),
                )
                if result.outcome is SourceDispatchExecutionOutcome.IDLE:
                    break
                counters = counters.add_dispatch(
                    succeeded=result.outcome is SourceDispatchExecutionOutcome.SUCCEEDED
                )
                cycle = self._heartbeat(
                    cycle,
                    command=command,
                    counters=counters,
                )

            for target in command.pipeline_targets:
                for run_index in range(target.max_runs):
                    self._heartbeat(cycle, command=command, counters=counters)
                    result = self._ingestion_worker.run_once(
                        worker_ref=command.worker_ref,
                        pipeline_code=target.pipeline_code,
                        pipeline_version=target.pipeline_version,
                        ttl_seconds=command.ingestion_ttl_seconds,
                        trace_id=(
                            f"cycle:{cycle.id}:ingestion:"
                            f"{target.pipeline_code}:{target.pipeline_version}:"
                            f"{run_index + 1}"
                        ),
                    )
                    if result.outcome is IngestionWorkerRunOutcome.IDLE:
                        break
                    counters = counters.add_ingestion(
                        succeeded=result.outcome is IngestionWorkerRunOutcome.SUCCEEDED
                    )
                    cycle = self._heartbeat(
                        cycle,
                        command=command,
                        counters=counters,
                    )

            terminal_state, outcome, error_code = self._terminal_outcome(counters)
            completed = self._complete(
                cycle,
                command=command,
                counters=counters,
                state=terminal_state,
                error_code=error_code,
            )
            return self._emit(
                self._result(
                    started_ns=started_ns,
                    outcome=outcome,
                    cycle=completed,
                )
            )
        except ContentSupplyCycleLeaseError as exc:
            return self._emit(
                self._result(
                    started_ns=started_ns,
                    outcome=ContentSupplyCycleOutcome.LEASE_LOST,
                    cycle=cycle,
                    counters=counters,
                    error_code=exc.code,
                )
            )
        except Exception:
            try:
                completed = self._complete(
                    cycle,
                    command=command,
                    counters=counters,
                    state=ContentSupplyCycleState.FAILED,
                    error_code="CONTENT_SUPPLY_CYCLE_UNEXPECTED_FAILURE",
                )
                return self._emit(
                    self._result(
                        started_ns=started_ns,
                        outcome=ContentSupplyCycleOutcome.FAILED,
                        cycle=completed,
                    )
                )
            except ContentSupplyCycleLeaseError as exc:
                return self._emit(
                    self._result(
                        started_ns=started_ns,
                        outcome=ContentSupplyCycleOutcome.LEASE_LOST,
                        cycle=cycle,
                        counters=counters,
                        error_code=exc.code,
                    )
                )

    def recover_stale(
        self,
        *,
        limit: int = 100,
        now=None,
    ) -> tuple[ContentSupplyCycle, ...]:
        if limit < 1 or limit > MAXIMUM_STALE_CYCLE_RECOVERY_BATCH:
            raise ValueError(
                "stale cycle recovery limit is outside the supported range"
            )
        return self._repository.recover_stale(
            at=now or self._clock(),
            limit=limit,
        )

    def _heartbeat(
        self,
        cycle: ContentSupplyCycle,
        *,
        command: ContentSupplyCycleCommand,
        counters: ContentSupplyCycleCounters,
    ) -> ContentSupplyCycle:
        at = self._clock()
        try:
            return self._repository.heartbeat(
                cycle_id=cycle.id,
                worker_ref=command.worker_ref,
                heartbeat_at=at,
                expires_at=at + timedelta(seconds=command.cycle_ttl_seconds),
                counters=counters,
            )
        except KeyError as exc:
            raise ContentSupplyCycleLeaseError(
                "CONTENT_SUPPLY_CYCLE_NOT_FOUND"
            ) from exc
        except ValueError as exc:
            raise ContentSupplyCycleLeaseError(
                "CONTENT_SUPPLY_CYCLE_LEASE_NOT_ACTIVE"
            ) from exc

    def _complete(
        self,
        cycle: ContentSupplyCycle,
        *,
        command: ContentSupplyCycleCommand,
        counters: ContentSupplyCycleCounters,
        state: ContentSupplyCycleState,
        error_code: str | None,
    ) -> ContentSupplyCycle:
        at = self._clock()
        try:
            return self._repository.complete(
                cycle_id=cycle.id,
                worker_ref=command.worker_ref,
                completed_at=at,
                state=state,
                counters=counters,
                error_code=error_code,
            )
        except KeyError as exc:
            raise ContentSupplyCycleLeaseError(
                "CONTENT_SUPPLY_CYCLE_NOT_FOUND"
            ) from exc
        except ValueError as exc:
            raise ContentSupplyCycleLeaseError(
                "CONTENT_SUPPLY_CYCLE_LEASE_NOT_ACTIVE"
            ) from exc

    @staticmethod
    def _terminal_outcome(
        counters: ContentSupplyCycleCounters,
    ) -> tuple[ContentSupplyCycleState, ContentSupplyCycleOutcome, str | None]:
        if counters.has_non_success:
            return (
                ContentSupplyCycleState.DEGRADED,
                ContentSupplyCycleOutcome.DEGRADED,
                "CONTENT_SUPPLY_DELEGATED_NON_SUCCESS",
            )
        if counters.planned_count + counters.total_delegated_attempts == 0:
            return (
                ContentSupplyCycleState.IDLE,
                ContentSupplyCycleOutcome.IDLE,
                None,
            )
        return (
            ContentSupplyCycleState.SUCCEEDED,
            ContentSupplyCycleOutcome.SUCCEEDED,
            None,
        )

    def _result(
        self,
        *,
        started_ns: int,
        outcome: ContentSupplyCycleOutcome,
        cycle: ContentSupplyCycle,
        counters: ContentSupplyCycleCounters | None = None,
        error_code: str | None = None,
    ) -> ContentSupplyCycleResult:
        resolved = counters or cycle.counters
        elapsed_ns = max(0, self._monotonic_clock() - started_ns)
        return ContentSupplyCycleResult(
            outcome=outcome,
            cycle_id=cycle.id,
            worker_ref=cycle.worker_ref,
            plan_hash=cycle.plan_hash,
            planned_count=resolved.planned_count,
            dispatch_attempted_count=resolved.dispatch_attempted_count,
            dispatch_succeeded_count=resolved.dispatch_succeeded_count,
            dispatch_non_success_count=resolved.dispatch_non_success_count,
            ingestion_attempted_count=resolved.ingestion_attempted_count,
            ingestion_succeeded_count=resolved.ingestion_succeeded_count,
            ingestion_non_success_count=resolved.ingestion_non_success_count,
            duration_ms=elapsed_ns // 1_000_000,
            error_code=error_code if error_code is not None else cycle.error_code,
        )

    def _emit(self, result: ContentSupplyCycleResult) -> ContentSupplyCycleResult:
        try:
            self._observer.record(result)
        except Exception:
            pass
        return result
