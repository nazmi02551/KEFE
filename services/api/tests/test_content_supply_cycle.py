from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from kefe_api.modules.content_supply_cycle.in_memory import (
    InMemoryContentSupplyCycleRepository,
)
from kefe_api.modules.content_supply_cycle.models import (
    ContentSupplyCycleCommand,
    ContentSupplyCycleState,
    ContentSupplyPipelineTarget,
)
from kefe_api.modules.content_supply_cycle.service import (
    ContentSupplyCycleOutcome,
    ContentSupplyCycleService,
    InMemoryContentSupplyCycleObserver,
)
from kefe_api.modules.ingestion_orchestration.worker_runtime import (
    IngestionWorkerRunOutcome,
    IngestionWorkerRunResult,
)
from kefe_api.modules.knowledge.source_scheduler_service import (
    SourceDispatchExecutionOutcome,
    SourceDispatchExecutionResult,
)


class MutableClock:
    def __init__(self, now: datetime) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now


class StubScheduler:
    def __init__(
        self,
        *,
        planned: list[object | None] | None = None,
        dispatch_outcomes: list[SourceDispatchExecutionOutcome] | None = None,
        fail_planning: bool = False,
    ) -> None:
        self.planned = list(planned or [])
        self.dispatch_outcomes = list(dispatch_outcomes or [])
        self.fail_planning = fail_planning
        self.calls: list[str] = []

    def plan_due_once(self, *, now=None):
        del now
        self.calls.append("plan")
        if self.fail_planning:
            raise RuntimeError("secret provider response")
        return self.planned.pop(0) if self.planned else None

    def execute_pending_once(
        self,
        *,
        worker_ref: str,
        ttl_seconds: int,
        trace_id: str | None = None,
        now=None,
    ) -> SourceDispatchExecutionResult:
        del ttl_seconds, trace_id, now
        self.calls.append("dispatch")
        outcome = (
            self.dispatch_outcomes.pop(0)
            if self.dispatch_outcomes
            else SourceDispatchExecutionOutcome.IDLE
        )
        return SourceDispatchExecutionResult(
            outcome=outcome,
            worker_ref=worker_ref,
            duration_ms=0,
            schedule_id=uuid4() if outcome is not SourceDispatchExecutionOutcome.IDLE else None,
            dispatch_id=uuid4() if outcome is not SourceDispatchExecutionOutcome.IDLE else None,
            error_code=(
                None
                if outcome
                in {
                    SourceDispatchExecutionOutcome.IDLE,
                    SourceDispatchExecutionOutcome.SUCCEEDED,
                }
                else "BOUNDED_DISPATCH_NON_SUCCESS"
            ),
        )


class StubIngestionWorker:
    def __init__(
        self,
        outcomes: dict[tuple[str, str], list[IngestionWorkerRunOutcome]] | None = None,
    ) -> None:
        self.outcomes = {key: list(value) for key, value in (outcomes or {}).items()}
        self.calls: list[str] = []

    def run_once(
        self,
        *,
        worker_ref: str,
        pipeline_code: str,
        pipeline_version: str,
        ttl_seconds: int,
        trace_id: str | None = None,
    ) -> IngestionWorkerRunResult:
        del ttl_seconds
        self.calls.append(f"ingestion:{pipeline_code}@{pipeline_version}")
        queue = self.outcomes.get((pipeline_code, pipeline_version), [])
        outcome = queue.pop(0) if queue else IngestionWorkerRunOutcome.IDLE
        return IngestionWorkerRunResult(
            outcome=outcome,
            worker_ref=worker_ref,
            pipeline_code=pipeline_code,
            pipeline_version=pipeline_version,
            trace_id=trace_id or "trace",
            duration_ms=0,
            run_id=uuid4() if outcome is not IngestionWorkerRunOutcome.IDLE else None,
            error_code=(
                None
                if outcome
                in {
                    IngestionWorkerRunOutcome.IDLE,
                    IngestionWorkerRunOutcome.SUCCEEDED,
                }
                else "BOUNDED_INGESTION_NON_SUCCESS"
            ),
        )


class ExplodingObserver:
    def record(self, result) -> None:
        del result
        raise RuntimeError("observer unavailable")


class ExpiringHeartbeatRepository(InMemoryContentSupplyCycleRepository):
    def heartbeat(self, **kwargs):
        self.recover_stale(
            at=kwargs["heartbeat_at"] + timedelta(seconds=6),
            limit=1,
        )
        return super().heartbeat(**kwargs)


def _command(
    *,
    plan_budget: int = 5,
    dispatch_budget: int = 5,
    max_runs: int = 5,
) -> ContentSupplyCycleCommand:
    return ContentSupplyCycleCommand(
        worker_ref="content-supply-worker",
        plan_budget=plan_budget,
        dispatch_budget=dispatch_budget,
        pipeline_targets=(
            ContentSupplyPipelineTarget(
                pipeline_code="NEWS_PIPELINE",
                pipeline_version="1.0.0",
                max_runs=max_runs,
            ),
        ),
        cycle_ttl_seconds=60,
        dispatch_ttl_seconds=30,
        ingestion_ttl_seconds=30,
    )


def _service(
    *,
    scheduler: StubScheduler,
    worker: StubIngestionWorker,
    repository=None,
    observer=None,
    clock=None,
):
    resolved_repository = repository or InMemoryContentSupplyCycleRepository()
    resolved_observer = observer or InMemoryContentSupplyCycleObserver()
    resolved_clock = clock or MutableClock(datetime(2026, 8, 2, 12, 0, tzinfo=UTC))
    return (
        resolved_repository,
        resolved_observer,
        ContentSupplyCycleService(
            repository=resolved_repository,
            scheduler=scheduler,
            ingestion_worker=worker,
            observer=resolved_observer,
            clock=resolved_clock,
        ),
    )


def test_cycle_command_plan_hash_is_deterministic_and_targets_are_exact() -> None:
    first = _command()
    second = _command()

    assert first.plan_hash == second.plan_hash
    assert len(first.plan_hash) == 64

    with pytest.raises(ValueError, match="duplicate"):
        ContentSupplyCycleCommand(
            worker_ref="worker",
            plan_budget=1,
            dispatch_budget=1,
            pipeline_targets=(
                ContentSupplyPipelineTarget("PIPE", "1", 1),
                ContentSupplyPipelineTarget("PIPE", "1", 2),
            ),
            cycle_ttl_seconds=10,
            dispatch_ttl_seconds=10,
            ingestion_ttl_seconds=10,
        )


def test_bounded_phase_order_stops_each_phase_on_idle() -> None:
    scheduler = StubScheduler(
        planned=[object(), None, object()],
        dispatch_outcomes=[
            SourceDispatchExecutionOutcome.SUCCEEDED,
            SourceDispatchExecutionOutcome.IDLE,
            SourceDispatchExecutionOutcome.SUCCEEDED,
        ],
    )
    worker = StubIngestionWorker(
        {
            ("NEWS_PIPELINE", "1.0.0"): [
                IngestionWorkerRunOutcome.SUCCEEDED,
                IngestionWorkerRunOutcome.IDLE,
                IngestionWorkerRunOutcome.SUCCEEDED,
            ]
        }
    )
    repository, observer, service = _service(scheduler=scheduler, worker=worker)

    result = service.run_once(_command())

    assert result.outcome is ContentSupplyCycleOutcome.SUCCEEDED
    assert result.planned_count == 1
    assert result.dispatch_attempted_count == 1
    assert result.dispatch_succeeded_count == 1
    assert result.ingestion_attempted_count == 1
    assert result.ingestion_succeeded_count == 1
    assert scheduler.calls == ["plan", "plan", "dispatch", "dispatch"]
    assert worker.calls == [
        "ingestion:NEWS_PIPELINE@1.0.0",
        "ingestion:NEWS_PIPELINE@1.0.0",
    ]
    stored = repository.get(result.cycle_id)
    assert stored is not None and stored.state is ContentSupplyCycleState.SUCCEEDED
    assert observer.results == [result]


def test_phase_budgets_bound_non_idle_work() -> None:
    scheduler = StubScheduler(
        planned=[object(), object(), object()],
        dispatch_outcomes=[
            SourceDispatchExecutionOutcome.SUCCEEDED,
            SourceDispatchExecutionOutcome.SUCCEEDED,
            SourceDispatchExecutionOutcome.SUCCEEDED,
        ],
    )
    worker = StubIngestionWorker(
        {
            ("NEWS_PIPELINE", "1.0.0"): [
                IngestionWorkerRunOutcome.SUCCEEDED,
                IngestionWorkerRunOutcome.SUCCEEDED,
                IngestionWorkerRunOutcome.SUCCEEDED,
            ]
        }
    )
    _, _, service = _service(scheduler=scheduler, worker=worker)

    result = service.run_once(
        _command(plan_budget=2, dispatch_budget=2, max_runs=2)
    )

    assert result.planned_count == 2
    assert result.dispatch_attempted_count == 2
    assert result.ingestion_attempted_count == 2
    assert len(scheduler.calls) == 4
    assert len(worker.calls) == 2


def test_no_delegated_work_completes_idle() -> None:
    repository, _, service = _service(
        scheduler=StubScheduler(),
        worker=StubIngestionWorker(),
    )

    result = service.run_once(_command())

    assert result.outcome is ContentSupplyCycleOutcome.IDLE
    assert repository.get(result.cycle_id).state is ContentSupplyCycleState.IDLE


def test_delegated_non_success_completes_degraded_without_retry_policy() -> None:
    scheduler = StubScheduler(
        dispatch_outcomes=[
            SourceDispatchExecutionOutcome.BLOCKED,
            SourceDispatchExecutionOutcome.IDLE,
        ]
    )
    worker = StubIngestionWorker(
        {
            ("NEWS_PIPELINE", "1.0.0"): [
                IngestionWorkerRunOutcome.RETRYABLE_FAILURE,
                IngestionWorkerRunOutcome.IDLE,
            ]
        }
    )
    repository, _, service = _service(scheduler=scheduler, worker=worker)

    result = service.run_once(_command(plan_budget=0))

    assert result.outcome is ContentSupplyCycleOutcome.DEGRADED
    assert result.dispatch_non_success_count == 1
    assert result.ingestion_non_success_count == 1
    assert result.error_code == "CONTENT_SUPPLY_DELEGATED_NON_SUCCESS"
    stored = repository.get(result.cycle_id)
    assert stored is not None and stored.state is ContentSupplyCycleState.DEGRADED


def test_unexpected_supervisor_failure_is_bounded_and_privacy_safe() -> None:
    repository, _, service = _service(
        scheduler=StubScheduler(fail_planning=True),
        worker=StubIngestionWorker(),
    )

    result = service.run_once(_command())

    assert result.outcome is ContentSupplyCycleOutcome.FAILED
    assert result.error_code == "CONTENT_SUPPLY_CYCLE_UNEXPECTED_FAILURE"
    assert "secret provider response" not in repr(result.as_operational_dict())
    assert repository.get(result.cycle_id).state is ContentSupplyCycleState.FAILED


def test_cycle_lease_loss_fails_closed_and_stale_cycle_is_abandoned() -> None:
    base = datetime(2026, 8, 2, 13, 0, tzinfo=UTC)
    repository = ExpiringHeartbeatRepository()
    _, _, service = _service(
        scheduler=StubScheduler(),
        worker=StubIngestionWorker(),
        repository=repository,
        clock=MutableClock(base),
    )
    command = ContentSupplyCycleCommand(
        worker_ref="expiring-worker",
        plan_budget=1,
        dispatch_budget=0,
        pipeline_targets=(),
        cycle_ttl_seconds=5,
        dispatch_ttl_seconds=5,
        ingestion_ttl_seconds=5,
    )

    result = service.run_once(command)

    assert result.outcome is ContentSupplyCycleOutcome.LEASE_LOST
    assert result.error_code == "CONTENT_SUPPLY_CYCLE_LEASE_NOT_ACTIVE"
    stored = repository.get(result.cycle_id)
    assert stored is not None and stored.state is ContentSupplyCycleState.ABANDONED
    assert stored.error_code == "CONTENT_SUPPLY_CYCLE_STALE"


def test_observer_failure_is_non_authoritative_and_result_allowlist_is_exact() -> None:
    _, _, service = _service(
        scheduler=StubScheduler(),
        worker=StubIngestionWorker(),
        observer=ExplodingObserver(),
    )

    result = service.run_once(_command())
    operational = result.as_operational_dict()

    assert result.outcome is ContentSupplyCycleOutcome.IDLE
    assert set(operational) == {
        "outcome",
        "cycle_id",
        "worker_ref",
        "plan_hash",
        "planned_count",
        "dispatch_attempted_count",
        "dispatch_succeeded_count",
        "dispatch_non_success_count",
        "ingestion_attempted_count",
        "ingestion_succeeded_count",
        "ingestion_non_success_count",
        "duration_ms",
        "error_code",
    }
    assert not {
        "external_locator",
        "raw_storage_ref",
        "proposal_payload",
        "provider_response",
        "credential",
        "user_id",
        "title",
    }.intersection(operational)
