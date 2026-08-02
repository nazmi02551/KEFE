from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text

from kefe_api.infrastructure.postgres_ingestion_orchestration import (
    PostgresIngestionOrchestrationRepository,
)
from kefe_api.infrastructure.postgres_knowledge import PostgresKnowledgeRepository
from kefe_api.infrastructure.postgres_source_acquisition_scheduler import (
    PostgresSourceAcquisitionSchedulerRepository,
)
from kefe_api.modules.ingestion_orchestration.service import (
    IngestionOrchestrationService,
)
from kefe_api.modules.knowledge.source_acquisition import (
    CapturedSource,
    InMemorySourceAcquisitionObserver,
    InMemorySourceCaptureRegistry,
    SourceAcquisitionService,
)
from kefe_api.modules.knowledge.source_scheduler import (
    SourceAcquisitionDispatchState,
)
from kefe_api.modules.knowledge.source_scheduler_service import (
    InMemorySourceDispatchObserver,
    SourceAcquisitionSchedulerService,
    SourceDispatchExecutionOutcome,
)

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)


@pytest.fixture(autouse=True)
def _isolate_scheduler_ledger():
    if os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1":
        yield
        return
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    with engine.begin() as connection:
        connection.execute(text("DELETE FROM knowledge.source_acquisition_dispatch"))
        connection.execute(text("DELETE FROM knowledge.source_acquisition_schedule"))
    yield


class CaptureAdapter:
    def __init__(self, *, adapter_code: str, content_hash: str) -> None:
        self._adapter_code = adapter_code
        self.content_hash = content_hash
        self.calls = 0

    @property
    def adapter_code(self) -> str:
        return self._adapter_code

    def capture(self, *, external_locator: str, trace_id: str) -> CapturedSource:
        del external_locator, trace_id
        self.calls += 1
        return CapturedSource(content_hash=self.content_hash)


def _runtime(*, engine, adapter: CaptureAdapter, clock):
    knowledge = PostgresKnowledgeRepository(engine)
    ingestion = PostgresIngestionOrchestrationRepository(engine)
    scheduler_repository = PostgresSourceAcquisitionSchedulerRepository(engine)
    acquisition = SourceAcquisitionService(
        knowledge_repository=knowledge,
        ingestion_service=IngestionOrchestrationService(ingestion),
        registry=InMemorySourceCaptureRegistry((adapter,)),
        observer=InMemorySourceAcquisitionObserver(),
        clock=clock,
    )
    scheduler = SourceAcquisitionSchedulerService(
        repository=scheduler_repository,
        acquisition=acquisition,
        observer=InMemorySourceDispatchObserver(),
        clock=clock,
    )
    return knowledge, ingestion, scheduler_repository, scheduler, acquisition


def _create_schedule(
    scheduler: SourceAcquisitionSchedulerService,
    *,
    adapter_code: str,
    locator: str,
    first_due_at: datetime,
    attempts: int = 3,
):
    return scheduler.create_schedule(
        adapter_code=adapter_code,
        external_locator=locator,
        pipeline_code="POSTGRES_SCHEDULED_SOURCE",
        pipeline_version="1.0.0",
        configuration_hash="sha256:postgres-scheduler-config",
        first_due_at=first_due_at,
        interval_seconds=300,
        max_dispatch_attempts=attempts,
        taxonomy_version="taxonomy-v1",
        methodology_version="methodology-v1",
        locale="en",
        jurisdiction_code="ZZ",
        now=first_due_at - timedelta(minutes=1),
    )


def test_postgres_concurrent_planners_create_one_unique_occurrence_without_drift() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    base = datetime.now(UTC).replace(microsecond=0)
    suffix = uuid4().hex[:10]
    adapter = CaptureAdapter(
        adapter_code=f"test.pg_scheduler_{suffix}.v1",
        content_hash=f"sha256:planner:{suffix}",
    )
    _, _, repository, scheduler, _ = _runtime(
        engine=engine,
        adapter=adapter,
        clock=lambda: base,
    )
    schedule = _create_schedule(
        scheduler,
        adapter_code=adapter.adapter_code,
        locator=f"https://example.test/scheduler/planner/{suffix}",
        first_due_at=base,
    )
    barrier = Barrier(2)

    def plan():
        barrier.wait()
        return PostgresSourceAcquisitionSchedulerRepository(engine).plan_due_once(
            at=base
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        planned = tuple(pool.map(lambda _: plan(), range(2)))

    non_null = tuple(item for item in planned if item is not None)
    assert len(non_null) == 1
    assert non_null[0].due_at == base
    stored = repository.get_schedule(schedule.id)
    assert stored is not None
    assert stored.next_due_at == base + timedelta(minutes=5)
    assert len(repository.list_dispatches(schedule.id)) == 1

    late = base + timedelta(minutes=20)
    second = repository.plan_due_once(at=late)
    third = repository.plan_due_once(at=late)
    assert second is not None and second.due_at == base + timedelta(minutes=5)
    assert third is not None and third.due_at == base + timedelta(minutes=10)
    assert repository.get_schedule(schedule.id).next_due_at == base + timedelta(
        minutes=15
    )


def test_postgres_concurrent_executors_never_complete_same_dispatch_twice() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    base = datetime.now(UTC).replace(microsecond=0)
    suffix = uuid4().hex[:10]
    adapter = CaptureAdapter(
        adapter_code=f"test.pg_executor_{suffix}.v1",
        content_hash=f"sha256:executor:{suffix}",
    )
    _, _, repository, scheduler, _ = _runtime(
        engine=engine,
        adapter=adapter,
        clock=lambda: base,
    )
    schedule = _create_schedule(
        scheduler,
        adapter_code=adapter.adapter_code,
        locator=f"https://example.test/scheduler/executor/{suffix}",
        first_due_at=base,
    )
    dispatch = scheduler.plan_due_once(now=base)
    assert dispatch is not None
    barrier = Barrier(2)

    def execute(worker_ref: str):
        _, _, _, worker_scheduler, _ = _runtime(
            engine=engine,
            adapter=adapter,
            clock=lambda: base,
        )
        barrier.wait()
        return worker_scheduler.execute_pending_once(
            worker_ref=worker_ref,
            ttl_seconds=60,
            now=base,
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = tuple(
            pool.map(execute, ("postgres-executor-one", "postgres-executor-two"))
        )

    assert sorted(result.outcome.value for result in results) == ["IDLE", "SUCCEEDED"]
    stored = repository.get_dispatch(dispatch.id)
    assert stored is not None
    assert stored.state is SourceAcquisitionDispatchState.SUCCEEDED
    assert stored.attempt_count == 1
    assert len(repository.list_dispatches(schedule.id)) == 1
    assert adapter.calls == 1


def test_postgres_stale_dispatch_recovery_exhausts_bounded_attempts() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    base = datetime.now(UTC).replace(microsecond=0)
    suffix = uuid4().hex[:10]
    adapter = CaptureAdapter(
        adapter_code=f"test.pg_stale_{suffix}.v1",
        content_hash=f"sha256:stale:{suffix}",
    )
    _, _, repository, scheduler, _ = _runtime(
        engine=engine,
        adapter=adapter,
        clock=lambda: base,
    )
    _create_schedule(
        scheduler,
        adapter_code=adapter.adapter_code,
        locator=f"https://example.test/scheduler/stale/{suffix}",
        first_due_at=base,
        attempts=2,
    )
    dispatch = scheduler.plan_due_once(now=base)
    assert dispatch is not None
    first = repository.claim_pending_once(
        worker_ref="stale-one",
        claimed_at=base,
        expires_at=base + timedelta(seconds=5),
    )
    assert first is not None
    recovered = repository.recover_stale(
        at=base + timedelta(seconds=6),
        limit=10,
    )
    assert recovered[0].state is SourceAcquisitionDispatchState.PENDING
    second = repository.claim_pending_once(
        worker_ref="stale-two",
        claimed_at=base + timedelta(seconds=7),
        expires_at=base + timedelta(seconds=12),
    )
    assert second is not None and second.dispatch.attempt_count == 2
    exhausted = repository.recover_stale(
        at=base + timedelta(seconds=13),
        limit=10,
    )
    assert exhausted[0].state is SourceAcquisitionDispatchState.FINAL_FAILURE
    assert exhausted[0].error_code == "SOURCE_DISPATCH_ATTEMPTS_EXHAUSTED"


def test_postgres_crash_after_acquisition_replays_same_ids_and_completes() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    base = datetime.now(UTC).replace(microsecond=0)
    suffix = uuid4().hex[:10]
    adapter = CaptureAdapter(
        adapter_code=f"test.pg_crash_{suffix}.v1",
        content_hash=f"sha256:crash:{suffix}",
    )
    knowledge, ingestion, repository, scheduler, acquisition = _runtime(
        engine=engine,
        adapter=adapter,
        clock=lambda: base,
    )
    _create_schedule(
        scheduler,
        adapter_code=adapter.adapter_code,
        locator=f"https://example.test/scheduler/crash/{suffix}",
        first_due_at=base,
    )
    dispatch = scheduler.plan_due_once(now=base)
    assert dispatch is not None
    claim = repository.claim_pending_once(
        worker_ref="crashed-postgres-worker",
        claimed_at=base,
        expires_at=base + timedelta(seconds=5),
    )
    assert claim is not None
    first_acquisition = acquisition.acquire(
        claim.schedule.acquisition_command(),
        trace_id="postgres-before-crash",
    )
    assert first_acquisition.source_artifact_id is not None
    assert first_acquisition.ingestion_run_id is not None

    repository.recover_stale(at=base + timedelta(seconds=6), limit=10)
    recovery_time = base + timedelta(seconds=7)
    _, _, _, recovery_scheduler, _ = _runtime(
        engine=engine,
        adapter=adapter,
        clock=lambda: recovery_time,
    )
    replayed = recovery_scheduler.execute_pending_once(
        worker_ref="postgres-recovery-worker",
        ttl_seconds=60,
        now=recovery_time,
        trace_id="postgres-after-crash",
    )

    assert replayed.outcome is SourceDispatchExecutionOutcome.SUCCEEDED
    assert replayed.source_artifact_id == first_acquisition.source_artifact_id
    assert replayed.ingestion_run_id == first_acquisition.ingestion_run_id
    assert knowledge.get_source_artifact(replayed.source_artifact_id) is not None
    assert ingestion.get_run(replayed.ingestion_run_id) is not None
    stored = repository.get_dispatch(dispatch.id)
    assert stored is not None and stored.state is SourceAcquisitionDispatchState.SUCCEEDED
