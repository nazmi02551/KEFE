from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import create_engine

from kefe_api.infrastructure.postgres_ingestion_orchestration import (
    PostgresIngestionOrchestrationRepository,
)
from kefe_api.infrastructure.postgres_ingestion_run_leases import (
    PostgresIngestionRunLeaseRepository,
)
from kefe_api.infrastructure.postgres_knowledge import PostgresKnowledgeRepository
from kefe_api.modules.ingestion_orchestration.lease_service import (
    IngestionRunLeaseService,
)
from kefe_api.modules.ingestion_orchestration.models import (
    ExecutorKind,
    IngestionRunState,
    InputArtifactKind,
    StageProcessorResult,
)
from kefe_api.modules.ingestion_orchestration.service import (
    IngestionOrchestrationService,
)
from kefe_api.modules.ingestion_orchestration.worker_runtime import (
    IngestionRuntimePlan,
    IngestionRuntimeStage,
    IngestionWorkerRunOutcome,
    InMemoryIngestionWorkerObserver,
    InMemoryIngestionWorkerRuntimeRegistry,
)
from kefe_api.modules.ingestion_orchestration.worker_service import (
    IngestionWorkerRunner,
)
from kefe_api.modules.knowledge.models import SourceArtifact

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)


class RecordingProcessor:
    def __init__(self, marker: str, before_return=None) -> None:
        self.marker = marker
        self.before_return = before_return
        self.inputs: list[str] = []
        self.last_result: StageProcessorResult | None = None

    def process(self, *, run, stage_code, stage_version, input_hash):
        del run, stage_code, stage_version
        self.inputs.append(input_hash)
        if self.before_return is not None:
            self.before_return()
        result = StageProcessorResult(output_metadata={"marker": self.marker})
        self.last_result = result
        return result


def _stage(code: str) -> IngestionRuntimeStage:
    return IngestionRuntimeStage(
        stage_code=code,
        stage_version="1.0.0",
        max_attempts=2,
        executor_kind=ExecutorKind.DETERMINISTIC,
    )


def _seed_run(
    *,
    engine,
    pipeline_code: str,
    pipeline_version: str,
):
    source = PostgresKnowledgeRepository(engine).add_source_artifact(
        SourceArtifact.create(
            adapter_code="ingestion-worker-runner-fixture",
            external_locator=f"https://example.test/worker-runner/{uuid4()}",
            content_hash=f"sha256:worker-runner:{uuid4()}",
            language_code="en",
        )
    )
    service = IngestionOrchestrationService(
        PostgresIngestionOrchestrationRepository(engine)
    )
    return service.start_run(
        input_artifact_kind=InputArtifactKind.SOURCE_ARTIFACT,
        input_artifact_id=source.id,
        input_content_hash=source.content_hash,
        pipeline_code=pipeline_code,
        pipeline_version=pipeline_version,
        configuration_hash="sha256:worker-runner-config",
    )


def _runner(
    *,
    repository,
    lease_repository,
    plan,
    processors,
    clock,
):
    orchestration = IngestionOrchestrationService(repository)
    leases = IngestionRunLeaseService(lease_repository)
    observer = InMemoryIngestionWorkerObserver()
    runner = IngestionWorkerRunner(
        repository=repository,
        orchestration=orchestration,
        leases=leases,
        registry=InMemoryIngestionWorkerRuntimeRegistry((plan,), processors),
        observer=observer,
        clock=clock,
    )
    return orchestration, leases, observer, runner


def test_postgres_worker_claim_filters_exact_pipeline_version() -> None:
    database_url = os.environ["KEFE_DATABASE_URL"]
    engine = create_engine(database_url)
    pipeline_code = f"RUNNER_VERSION_{uuid4().hex[:10]}"
    old_run = _seed_run(
        engine=engine,
        pipeline_code=pipeline_code,
        pipeline_version="1.0.0",
    )
    selected_run = _seed_run(
        engine=engine,
        pipeline_code=pipeline_code,
        pipeline_version="2.0.0",
    )
    plan = IngestionRuntimePlan(
        pipeline_code=pipeline_code,
        pipeline_version="2.0.0",
        stages=(_stage("EXTRACT"),),
    )
    processor = RecordingProcessor("version-two")
    repository = PostgresIngestionOrchestrationRepository(engine)
    lease_repository = PostgresIngestionRunLeaseRepository(engine)
    _, _, observer, runner = _runner(
        repository=repository,
        lease_repository=lease_repository,
        plan=plan,
        processors={
            (pipeline_code, "2.0.0", "EXTRACT", "1.0.0"): processor
        },
        clock=lambda: datetime.now(UTC),
    )

    result = runner.run_once(
        worker_ref="postgres-worker-v2",
        pipeline_code=pipeline_code,
        pipeline_version="2.0.0",
        ttl_seconds=60,
        trace_id="postgres-exact-version",
    )

    assert result.outcome is IngestionWorkerRunOutcome.SUCCEEDED
    assert result.run_id == selected_run.id
    assert repository.get_run(old_run.id).state is IngestionRunState.QUEUED
    assert repository.get_run(selected_run.id).state is IngestionRunState.SUCCEEDED
    assert len(observer.results) == 1


def test_postgres_worker_crash_recovery_resumes_after_successful_stage() -> None:
    database_url = os.environ["KEFE_DATABASE_URL"]
    engine = create_engine(database_url)
    pipeline_code = f"RUNNER_RESUME_{uuid4().hex[:10]}"
    run = _seed_run(
        engine=engine,
        pipeline_code=pipeline_code,
        pipeline_version="1.0.0",
    )
    plan = IngestionRuntimePlan(
        pipeline_code=pipeline_code,
        pipeline_version="1.0.0",
        stages=(_stage("FIRST"), _stage("SECOND")),
    )
    repository = PostgresIngestionOrchestrationRepository(engine)
    lease_repository = PostgresIngestionRunLeaseRepository(engine)
    base = datetime.now(UTC)
    first_processor = RecordingProcessor("first")
    first_orchestration = IngestionOrchestrationService(repository)
    leases = IngestionRunLeaseService(lease_repository)
    expiring_second = RecordingProcessor(
        "second-expired",
        before_return=lambda: leases.recover_expired(
            now=base + timedelta(seconds=6)
        ),
    )
    first_observer = InMemoryIngestionWorkerObserver()
    first_runner = IngestionWorkerRunner(
        repository=repository,
        orchestration=first_orchestration,
        leases=leases,
        registry=InMemoryIngestionWorkerRuntimeRegistry(
            (plan,),
            {
                (pipeline_code, "1.0.0", "FIRST", "1.0.0"): first_processor,
                (pipeline_code, "1.0.0", "SECOND", "1.0.0"): expiring_second,
            },
        ),
        observer=first_observer,
        clock=lambda: base,
    )

    interrupted = first_runner.run_once(
        worker_ref="postgres-worker-one",
        pipeline_code=pipeline_code,
        pipeline_version="1.0.0",
        ttl_seconds=5,
        trace_id="postgres-first-claim",
    )

    assert interrupted.outcome is IngestionWorkerRunOutcome.LEASE_LOST
    assert repository.get_run(run.id).state is IngestionRunState.QUEUED
    assert len(repository.list_stage_executions(run.id)) == 1

    resumed_second = RecordingProcessor("second-success")
    second_observer = InMemoryIngestionWorkerObserver()
    second_runner = IngestionWorkerRunner(
        repository=repository,
        orchestration=IngestionOrchestrationService(repository),
        leases=leases,
        registry=InMemoryIngestionWorkerRuntimeRegistry(
            (plan,),
            {
                (pipeline_code, "1.0.0", "FIRST", "1.0.0"): first_processor,
                (pipeline_code, "1.0.0", "SECOND", "1.0.0"): resumed_second,
            },
        ),
        observer=second_observer,
        clock=lambda: base + timedelta(seconds=7),
    )

    resumed = second_runner.run_once(
        worker_ref="postgres-worker-two",
        pipeline_code=pipeline_code,
        pipeline_version="1.0.0",
        ttl_seconds=60,
        trace_id="postgres-second-claim",
    )

    assert resumed.outcome is IngestionWorkerRunOutcome.SUCCEEDED
    assert first_processor.inputs == [run.input_content_hash]
    assert first_processor.last_result is not None
    assert resumed_second.inputs == [first_processor.last_result.output_hash]
    assert len(repository.list_stage_executions(run.id)) == 2
    assert repository.get_run(run.id).state is IngestionRunState.SUCCEEDED
    assert len(first_observer.results) == 1
    assert len(second_observer.results) == 1
