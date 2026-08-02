from __future__ import annotations

from datetime import UTC, datetime

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
)
from kefe_api.modules.knowledge.source_scheduler_memory import (
    InMemorySourceAcquisitionSchedulerRepository,
)
from kefe_api.modules.knowledge.source_scheduler_service import (
    SourceAcquisitionSchedulerService,
    SourceDispatchExecutionOutcome,
)


class CaptureAdapter:
    adapter_code = "test.scheduler_edges.v1"

    def capture(self, *, external_locator: str, trace_id: str) -> CapturedSource:
        del external_locator, trace_id
        return CapturedSource(content_hash="sha256:scheduler-edges")


class ExplodingDispatchObserver:
    def record(self, result) -> None:
        del result
        raise RuntimeError("observer unavailable")


def _service(*, registry, observer):
    base = datetime(2026, 8, 2, 16, 0, tzinfo=UTC)
    knowledge = InMemoryKnowledgeRepository()
    ingestion = InMemoryIngestionOrchestrationRepository()
    repository = InMemorySourceAcquisitionSchedulerRepository()
    acquisition = SourceAcquisitionService(
        knowledge_repository=knowledge,
        ingestion_service=IngestionOrchestrationService(ingestion),
        registry=registry,
        observer=InMemorySourceAcquisitionObserver(),
        clock=lambda: base,
    )
    scheduler = SourceAcquisitionSchedulerService(
        repository=repository,
        acquisition=acquisition,
        observer=observer,
        clock=lambda: base,
    )
    schedule = scheduler.create_schedule(
        adapter_code="test.scheduler_edges.v1",
        external_locator="https://example.test/scheduler/edges",
        pipeline_code="SCHEDULER_EDGES",
        pipeline_version="1.0.0",
        configuration_hash="sha256:scheduler-edges-config",
        first_due_at=base,
        interval_seconds=300,
        max_dispatch_attempts=2,
        now=base,
    )
    dispatch = scheduler.plan_due_once(now=base)
    assert dispatch is not None
    return base, knowledge, ingestion, repository, schedule, dispatch, scheduler


def test_missing_adapter_maps_dispatch_to_blocked_terminal_state() -> None:
    (
        base,
        knowledge,
        ingestion,
        repository,
        _,
        dispatch,
        scheduler,
    ) = _service(
        registry=InMemorySourceCaptureRegistry(),
        observer=ExplodingDispatchObserver(),
    )

    result = scheduler.execute_pending_once(
        worker_ref="blocked-worker",
        ttl_seconds=60,
        now=base,
    )

    assert result.outcome is SourceDispatchExecutionOutcome.BLOCKED
    assert result.error_code == "SOURCE_CAPTURE_ADAPTER_NOT_REGISTERED"
    stored = repository.get_dispatch(dispatch.id)
    assert stored is not None
    assert stored.state is SourceAcquisitionDispatchState.BLOCKED
    assert stored.error_code == "SOURCE_CAPTURE_ADAPTER_NOT_REGISTERED"
    assert knowledge._source_artifacts == {}
    assert ingestion._runs == {}


def test_dispatch_observer_failure_does_not_change_successful_completion() -> None:
    (
        base,
        knowledge,
        ingestion,
        repository,
        _,
        dispatch,
        scheduler,
    ) = _service(
        registry=InMemorySourceCaptureRegistry((CaptureAdapter(),)),
        observer=ExplodingDispatchObserver(),
    )

    result = scheduler.execute_pending_once(
        worker_ref="observer-worker",
        ttl_seconds=60,
        now=base,
    )

    assert result.outcome is SourceDispatchExecutionOutcome.SUCCEEDED
    assert result.source_artifact_id is not None
    assert result.ingestion_run_id is not None
    assert knowledge.get_source_artifact(result.source_artifact_id) is not None
    assert ingestion.get_run(result.ingestion_run_id) is not None
    stored = repository.get_dispatch(dispatch.id)
    assert stored is not None
    assert stored.state is SourceAcquisitionDispatchState.SUCCEEDED
