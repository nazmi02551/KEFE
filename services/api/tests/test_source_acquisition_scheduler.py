from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from kefe_api.modules.ingestion_orchestration.in_memory import (
    InMemoryIngestionOrchestrationRepository,
)
from kefe_api.modules.ingestion_orchestration.service import (
    IngestionOrchestrationService,
)
from kefe_api.modules.knowledge.in_memory import InMemoryKnowledgeRepository
from kefe_api.modules.knowledge.source_acquisition import (
    CapturedSource,
    InMemorySourceAcquisitionObserver,
    InMemorySourceCaptureRegistry,
    SourceAcquisitionService,
)
from kefe_api.modules.knowledge.source_scheduler import (
    SourceAcquisitionDispatchState,
    SourceAcquisitionScheduleState,
)
from kefe_api.modules.knowledge.source_scheduler_memory import (
    InMemorySourceAcquisitionSchedulerRepository,
)
from kefe_api.modules.knowledge.source_scheduler_service import (
    InMemorySourceDispatchObserver,
    SourceAcquisitionSchedulerService,
    SourceDispatchExecutionOutcome,
)


class MutableClock:
    def __init__(self, now: datetime) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now


class CaptureAdapter:
    def __init__(
        self,
        *,
        content_hash: str,
        before_return=None,
        adapter_code: str = "test.scheduler.v1",
    ) -> None:
        self._adapter_code = adapter_code
        self.content_hash = content_hash
        self.before_return = before_return
        self.calls = 0

    @property
    def adapter_code(self) -> str:
        return self._adapter_code

    def capture(self, *, external_locator: str, trace_id: str) -> CapturedSource:
        del external_locator, trace_id
        self.calls += 1
        if self.before_return is not None:
            self.before_return()
        return CapturedSource(
            content_hash=self.content_hash,
            raw_storage_ref="object://scheduler/raw-secret",
        )


class RecoverAfterArtifactKnowledgeRepository:
    def __init__(self, delegate, recover) -> None:
        self._delegate = delegate
        self._recover = recover

    def __getattr__(self, name):
        return getattr(self._delegate, name)

    def add_source_artifact(self, artifact):
        persisted = self._delegate.add_source_artifact(artifact)
        self._recover()
        return persisted


def _runtime(*, base: datetime, adapter: CaptureAdapter, knowledge=None):
    clock = MutableClock(base)
    knowledge_repository = knowledge or InMemoryKnowledgeRepository()
    ingestion_repository = InMemoryIngestionOrchestrationRepository()
    scheduler_repository = InMemorySourceAcquisitionSchedulerRepository()
    acquisition = SourceAcquisitionService(
        knowledge_repository=knowledge_repository,
        ingestion_service=IngestionOrchestrationService(ingestion_repository),
        registry=InMemorySourceCaptureRegistry((adapter,)),
        observer=InMemorySourceAcquisitionObserver(),
        clock=clock,
    )
    observer = InMemorySourceDispatchObserver()
    scheduler = SourceAcquisitionSchedulerService(
        repository=scheduler_repository,
        acquisition=acquisition,
        observer=observer,
        clock=clock,
    )
    return (
        clock,
        knowledge_repository,
        ingestion_repository,
        scheduler_repository,
        observer,
        scheduler,
        acquisition,
    )


def _schedule(scheduler, *, first_due_at, attempts: int = 3):
    return scheduler.create_schedule(
        adapter_code="test.scheduler.v1",
        external_locator="https://example.test/scheduled/source",
        pipeline_code="SCHEDULED_SOURCE_PIPELINE",
        pipeline_version="1.0.0",
        configuration_hash="sha256:scheduler-config",
        first_due_at=first_due_at,
        interval_seconds=300,
        max_dispatch_attempts=attempts,
        taxonomy_version="taxonomy-v1",
        methodology_version="methodology-v1",
        locale="en",
        jurisdiction_code="ZZ",
        now=first_due_at - timedelta(minutes=1),
    )


def test_fixed_interval_planning_has_no_drift_and_lifecycle_is_explicit() -> None:
    base = datetime(2026, 8, 2, 10, 0, tzinfo=UTC)
    adapter = CaptureAdapter(content_hash="sha256:no-drift")
    clock, _, _, repository, _, scheduler, _ = _runtime(
        base=base,
        adapter=adapter,
    )
    schedule = _schedule(scheduler, first_due_at=base)

    paused = scheduler.pause(schedule.id, now=base - timedelta(seconds=30))
    assert paused.state is SourceAcquisitionScheduleState.PAUSED
    assert scheduler.plan_due_once(now=base + timedelta(minutes=20)) is None

    resumed = scheduler.resume(schedule.id, now=base + timedelta(minutes=20))
    assert resumed.state is SourceAcquisitionScheduleState.ACTIVE
    first = scheduler.plan_due_once(now=base + timedelta(minutes=20))
    second = scheduler.plan_due_once(now=base + timedelta(minutes=20))

    assert first is not None and first.due_at == base
    assert second is not None and second.due_at == base + timedelta(minutes=5)
    stored = repository.get_schedule(schedule.id)
    assert stored is not None
    assert stored.next_due_at == base + timedelta(minutes=10)
    assert len(repository.list_dispatches(schedule.id)) == 2

    clock.now = base + timedelta(minutes=21)
    retired = scheduler.retire(schedule.id)
    assert retired.state is SourceAcquisitionScheduleState.RETIRED
    assert scheduler.plan_due_once(now=base + timedelta(days=1)) is None
    with pytest.raises(ValueError):
        scheduler.resume(schedule.id, now=base + timedelta(days=1))


def test_successful_dispatch_persists_only_artifact_and_run_identifiers() -> None:
    base = datetime(2026, 8, 2, 11, 0, tzinfo=UTC)
    adapter = CaptureAdapter(content_hash="sha256:dispatch-success")
    (
        _,
        knowledge,
        ingestion,
        repository,
        observer,
        scheduler,
        _,
    ) = _runtime(base=base, adapter=adapter)
    schedule = _schedule(scheduler, first_due_at=base)
    dispatch = scheduler.plan_due_once(now=base)
    assert dispatch is not None

    result = scheduler.execute_pending_once(
        worker_ref="scheduler-worker",
        ttl_seconds=60,
        trace_id="trace-dispatch-success",
        now=base,
    )

    assert result.outcome is SourceDispatchExecutionOutcome.SUCCEEDED
    stored = repository.get_dispatch(dispatch.id)
    assert stored is not None
    assert stored.state is SourceAcquisitionDispatchState.SUCCEEDED
    assert stored.source_artifact_id == result.source_artifact_id
    assert stored.ingestion_run_id == result.ingestion_run_id
    assert knowledge.get_source_artifact(result.source_artifact_id) is not None
    assert ingestion.get_run(result.ingestion_run_id) is not None
    operational = observer.results[0].as_operational_dict()
    assert set(operational) == {
        "outcome",
        "worker_ref",
        "schedule_id",
        "dispatch_id",
        "due_at",
        "attempt_count",
        "source_artifact_id",
        "ingestion_run_id",
        "duration_ms",
        "error_code",
    }
    assert "object://scheduler/raw-secret" not in repr(operational)
    assert repository.get_schedule(schedule.id) is not None


def test_exclusive_claim_owner_enforcement_stale_recovery_and_exhaustion() -> None:
    base = datetime(2026, 8, 2, 12, 0, tzinfo=UTC)
    adapter = CaptureAdapter(content_hash="sha256:lease")
    _, _, _, repository, _, scheduler, _ = _runtime(base=base, adapter=adapter)
    schedule = _schedule(scheduler, first_due_at=base, attempts=2)
    dispatch = scheduler.plan_due_once(now=base)
    assert dispatch is not None

    first = repository.claim_pending_once(
        worker_ref="worker-one",
        claimed_at=base,
        expires_at=base + timedelta(seconds=5),
    )
    assert first is not None
    assert repository.claim_pending_once(
        worker_ref="worker-two",
        claimed_at=base,
        expires_at=base + timedelta(seconds=5),
    ) is None
    with pytest.raises(ValueError):
        repository.heartbeat(
            dispatch_id=dispatch.id,
            worker_ref="worker-two",
            heartbeat_at=base + timedelta(seconds=1),
            expires_at=base + timedelta(seconds=6),
        )

    recovered = scheduler.recover_stale(now=base + timedelta(seconds=6))
    assert recovered[0].state is SourceAcquisitionDispatchState.PENDING
    second = repository.claim_pending_once(
        worker_ref="worker-two",
        claimed_at=base + timedelta(seconds=7),
        expires_at=base + timedelta(seconds=12),
    )
    assert second is not None and second.dispatch.attempt_count == 2
    exhausted = scheduler.recover_stale(now=base + timedelta(seconds=13))
    assert exhausted[0].state is SourceAcquisitionDispatchState.FINAL_FAILURE
    assert exhausted[0].error_code == "SOURCE_DISPATCH_ATTEMPTS_EXHAUSTED"
    assert repository.get_schedule(schedule.id) is not None


def test_lease_loss_before_artifact_persistence_produces_zero_writes() -> None:
    base = datetime(2026, 8, 2, 13, 0, tzinfo=UTC)
    repository_holder = {}
    adapter = CaptureAdapter(
        content_hash="sha256:expired-before-artifact",
        before_return=lambda: repository_holder["repository"].recover_stale(
            at=base + timedelta(seconds=6),
            limit=10,
        ),
    )
    (
        _,
        knowledge,
        ingestion,
        repository,
        _,
        scheduler,
        _,
    ) = _runtime(base=base, adapter=adapter)
    repository_holder["repository"] = repository
    _schedule(scheduler, first_due_at=base)
    dispatch = scheduler.plan_due_once(now=base)
    assert dispatch is not None

    result = scheduler.execute_pending_once(
        worker_ref="expired-worker",
        ttl_seconds=5,
        now=base,
    )

    assert result.outcome is SourceDispatchExecutionOutcome.LEASE_LOST
    assert knowledge._source_artifacts == {}
    assert ingestion._runs == {}
    stored = repository.get_dispatch(dispatch.id)
    assert stored is not None and stored.state is SourceAcquisitionDispatchState.PENDING


def test_lease_loss_before_run_admission_leaves_replayable_artifact() -> None:
    base = datetime(2026, 8, 2, 14, 0, tzinfo=UTC)
    knowledge = InMemoryKnowledgeRepository()
    repository = InMemorySourceAcquisitionSchedulerRepository()
    clock = MutableClock(base)
    ingestion = InMemoryIngestionOrchestrationRepository()
    adapter = CaptureAdapter(content_hash="sha256:artifact-before-run")
    guarded_knowledge = RecoverAfterArtifactKnowledgeRepository(
        knowledge,
        lambda: repository.recover_stale(
            at=base + timedelta(seconds=6),
            limit=10,
        ),
    )
    first_acquisition = SourceAcquisitionService(
        knowledge_repository=guarded_knowledge,
        ingestion_service=IngestionOrchestrationService(ingestion),
        registry=InMemorySourceCaptureRegistry((adapter,)),
        observer=InMemorySourceAcquisitionObserver(),
        clock=clock,
    )
    scheduler = SourceAcquisitionSchedulerService(
        repository=repository,
        acquisition=first_acquisition,
        observer=InMemorySourceDispatchObserver(),
        clock=clock,
    )
    _schedule(scheduler, first_due_at=base)
    dispatch = scheduler.plan_due_once(now=base)
    assert dispatch is not None

    interrupted = scheduler.execute_pending_once(
        worker_ref="worker-one",
        ttl_seconds=5,
        now=base,
    )

    assert interrupted.outcome is SourceDispatchExecutionOutcome.LEASE_LOST
    assert len(knowledge._source_artifacts) == 1
    assert ingestion._runs == {}
    assert repository.get_dispatch(dispatch.id).state is (
        SourceAcquisitionDispatchState.PENDING
    )

    clock.now = base + timedelta(seconds=7)
    replay_acquisition = SourceAcquisitionService(
        knowledge_repository=knowledge,
        ingestion_service=IngestionOrchestrationService(ingestion),
        registry=InMemorySourceCaptureRegistry((adapter,)),
        observer=InMemorySourceAcquisitionObserver(),
        clock=clock,
    )
    replay_scheduler = SourceAcquisitionSchedulerService(
        repository=repository,
        acquisition=replay_acquisition,
        observer=InMemorySourceDispatchObserver(),
        clock=clock,
    )
    completed = replay_scheduler.execute_pending_once(
        worker_ref="worker-two",
        ttl_seconds=60,
        now=clock.now,
    )

    assert completed.outcome is SourceDispatchExecutionOutcome.SUCCEEDED
    assert len(knowledge._source_artifacts) == 1
    assert len(ingestion._runs) == 1
    stored = repository.get_dispatch(dispatch.id)
    assert stored is not None and stored.state is SourceAcquisitionDispatchState.SUCCEEDED


def test_crash_after_acquisition_replays_same_ids_and_completes_dispatch() -> None:
    base = datetime(2026, 8, 2, 15, 0, tzinfo=UTC)
    adapter = CaptureAdapter(content_hash="sha256:crash-replay")
    (
        clock,
        knowledge,
        ingestion,
        repository,
        _,
        scheduler,
        acquisition,
    ) = _runtime(base=base, adapter=adapter)
    _schedule(scheduler, first_due_at=base)
    dispatch = scheduler.plan_due_once(now=base)
    assert dispatch is not None
    claim = repository.claim_pending_once(
        worker_ref="crashed-worker",
        claimed_at=base,
        expires_at=base + timedelta(seconds=5),
    )
    assert claim is not None

    first_acquisition = acquisition.acquire(
        claim.schedule.acquisition_command(),
        trace_id="trace-before-crash",
    )
    assert first_acquisition.source_artifact_id is not None
    assert first_acquisition.ingestion_run_id is not None

    repository.recover_stale(at=base + timedelta(seconds=6), limit=10)
    clock.now = base + timedelta(seconds=7)
    replayed = scheduler.execute_pending_once(
        worker_ref="recovery-worker",
        ttl_seconds=60,
        now=clock.now,
        trace_id="trace-after-crash",
    )

    assert replayed.outcome is SourceDispatchExecutionOutcome.SUCCEEDED
    assert replayed.source_artifact_id == first_acquisition.source_artifact_id
    assert replayed.ingestion_run_id == first_acquisition.ingestion_run_id
    assert len(knowledge._source_artifacts) == 1
    assert len(ingestion._runs) == 1
    assert repository.get_dispatch(dispatch.id).state is (
        SourceAcquisitionDispatchState.SUCCEEDED
    )
