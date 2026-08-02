from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from kefe_api.modules.ingestion_orchestration.in_memory import (
    InMemoryIngestionOrchestrationRepository,
)
from kefe_api.modules.ingestion_orchestration.in_memory_leases import (
    InMemoryIngestionRunLeaseRepository,
)
from kefe_api.modules.ingestion_orchestration.lease_service import (
    IngestionRunLeaseService,
)
from kefe_api.modules.ingestion_orchestration.leases import IngestionRunLeaseState
from kefe_api.modules.ingestion_orchestration.models import (
    ExecutorKind,
    IngestionRunState,
    InputArtifactKind,
    ProposalDraft,
    StageProcessorResult,
)
from kefe_api.modules.ingestion_orchestration.service import (
    FinalStageError,
    IngestionOrchestrationService,
    RetryableStageError,
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


class RecordingProcessor:
    def __init__(
        self,
        *,
        marker: str,
        proposal_payload: dict[str, object] | None = None,
        before_return=None,
    ) -> None:
        self.marker = marker
        self.proposal_payload = proposal_payload
        self.before_return = before_return
        self.inputs: list[str] = []
        self.last_result: StageProcessorResult | None = None

    def process(self, *, run, stage_code, stage_version, input_hash):
        del run, stage_code, stage_version
        self.inputs.append(input_hash)
        if self.before_return is not None:
            self.before_return()
        proposals = ()
        if self.proposal_payload is not None:
            proposals = (
                ProposalDraft(
                    proposal_kind="TEST_PROPOSAL",
                    payload_schema_ref="kefe.test-proposal",
                    payload_schema_version="1.0.0",
                    payload=self.proposal_payload,
                    provenance_ref="test:worker-runner",
                ),
            )
        result = StageProcessorResult(
            proposals=proposals,
            output_metadata={"marker": self.marker},
        )
        self.last_result = result
        return result


class RetryableProcessor:
    def process(self, *, run, stage_code, stage_version, input_hash):
        del run, stage_code, stage_version, input_hash
        raise RetryableStageError("TEMPORARY_TEST_FAILURE")


class FinalProcessor:
    def process(self, *, run, stage_code, stage_version, input_hash):
        del run, stage_code, stage_version, input_hash
        raise FinalStageError("FINAL_TEST_FAILURE")


def _stage(code: str, *, attempts: int = 2) -> IngestionRuntimeStage:
    return IngestionRuntimeStage(
        stage_code=code,
        stage_version="1.0.0",
        max_attempts=attempts,
        executor_kind=ExecutorKind.DETERMINISTIC,
    )


def _plan(*stages: IngestionRuntimeStage, version: str = "1.0.0"):
    return IngestionRuntimePlan(
        pipeline_code="TEST_PIPELINE",
        pipeline_version=version,
        stages=tuple(stages),
    )


def _processor_key(stage_code: str, *, version: str = "1.0.0"):
    return "TEST_PIPELINE", version, stage_code, "1.0.0"


def _runtime(plan, processors, *, clock=None):
    repository = InMemoryIngestionOrchestrationRepository()
    lease_repository = InMemoryIngestionRunLeaseRepository(repository)
    orchestration = IngestionOrchestrationService(repository)
    leases = IngestionRunLeaseService(lease_repository)
    observer = InMemoryIngestionWorkerObserver()
    runner = IngestionWorkerRunner(
        repository=repository,
        orchestration=orchestration,
        leases=leases,
        registry=InMemoryIngestionWorkerRuntimeRegistry((plan,), processors),
        observer=observer,
        clock=clock or (lambda: datetime.now(UTC)),
    )
    return repository, lease_repository, orchestration, leases, observer, runner


def _start(orchestration, *, version: str = "1.0.0"):
    return orchestration.start_run(
        input_artifact_kind=InputArtifactKind.SOURCE_ARTIFACT,
        input_artifact_id=uuid4(),
        input_content_hash=f"sha256:source:{uuid4()}",
        pipeline_code="TEST_PIPELINE",
        pipeline_version=version,
        configuration_hash="sha256:test-config",
    )


def test_worker_claims_exact_pipeline_version_and_reports_idle() -> None:
    processor = RecordingProcessor(marker="version-two")
    plan = _plan(_stage("EXTRACT"), version="2.0.0")
    repository, _, orchestration, _, observer, runner = _runtime(
        plan,
        {_processor_key("EXTRACT", version="2.0.0"): processor},
    )
    old_version = _start(orchestration, version="1.0.0")
    selected = _start(orchestration, version="2.0.0")

    first = runner.run_once(
        worker_ref="worker-v2",
        pipeline_code="TEST_PIPELINE",
        pipeline_version="2.0.0",
        ttl_seconds=60,
        trace_id="trace-version-two",
    )
    second = runner.run_once(
        worker_ref="worker-v2",
        pipeline_code="TEST_PIPELINE",
        pipeline_version="2.0.0",
        ttl_seconds=60,
        trace_id="trace-idle",
    )

    assert first.outcome is IngestionWorkerRunOutcome.SUCCEEDED
    assert first.run_id == selected.id
    assert second.outcome is IngestionWorkerRunOutcome.IDLE
    assert repository.get_run(old_version.id).state is IngestionRunState.QUEUED
    assert repository.get_run(selected.id).state is IngestionRunState.SUCCEEDED
    assert len(observer.results) == 2


def test_worker_executes_hash_chained_plan_and_exposes_no_payload() -> None:
    first_processor = RecordingProcessor(
        marker="normalized",
        proposal_payload={"secret_source_payload": "never-observe-this"},
    )
    second_processor = RecordingProcessor(marker="candidate")
    plan = _plan(_stage("NORMALIZE"), _stage("PROPOSE"))
    repository, _, orchestration, _, observer, runner = _runtime(
        plan,
        {
            _processor_key("NORMALIZE"): first_processor,
            _processor_key("PROPOSE"): second_processor,
        },
    )
    run = _start(orchestration)

    result = runner.run_once(
        worker_ref="worker-chain",
        pipeline_code=plan.pipeline_code,
        pipeline_version=plan.pipeline_version,
        ttl_seconds=60,
        trace_id="trace-chain",
    )

    assert result.outcome is IngestionWorkerRunOutcome.SUCCEEDED
    assert result.completed_stage_count == 2
    assert first_processor.inputs == [run.input_content_hash]
    assert first_processor.last_result is not None
    assert second_processor.inputs == [first_processor.last_result.output_hash]
    assert repository.get_run(run.id).state is IngestionRunState.SUCCEEDED
    assert len(repository.list_stage_executions(run.id)) == 2
    assert len(repository.list_proposals(run.id)) == 1
    operational = observer.results[0].as_operational_dict()
    assert set(operational) == {
        "outcome",
        "worker_ref",
        "pipeline_code",
        "pipeline_version",
        "trace_id",
        "run_id",
        "lease_id",
        "stage_code",
        "stage_version",
        "completed_stage_count",
        "stage_attempt",
        "duration_ms",
        "error_code",
    }
    assert "never-observe-this" not in repr(operational)


def test_lease_loss_before_persistence_leaves_zero_stage_output() -> None:
    base = datetime(2026, 8, 2, 8, 0, tzinfo=UTC)
    plan = _plan(_stage("EXTRACT"))
    repository = InMemoryIngestionOrchestrationRepository()
    lease_repository = InMemoryIngestionRunLeaseRepository(repository)
    orchestration = IngestionOrchestrationService(repository)
    leases = IngestionRunLeaseService(lease_repository)
    observer = InMemoryIngestionWorkerObserver()
    processor = RecordingProcessor(
        marker="must-not-persist",
        proposal_payload={"payload": "must-not-persist"},
        before_return=lambda: leases.recover_expired(
            now=base + timedelta(seconds=6)
        ),
    )
    runner = IngestionWorkerRunner(
        repository=repository,
        orchestration=orchestration,
        leases=leases,
        registry=InMemoryIngestionWorkerRuntimeRegistry(
            (plan,),
            {_processor_key("EXTRACT"): processor},
        ),
        observer=observer,
        clock=lambda: base,
    )
    run = _start(orchestration)

    result = runner.run_once(
        worker_ref="worker-expired",
        pipeline_code=plan.pipeline_code,
        pipeline_version=plan.pipeline_version,
        ttl_seconds=5,
        trace_id="trace-expired",
    )

    assert result.outcome is IngestionWorkerRunOutcome.LEASE_LOST
    assert repository.list_stage_executions(run.id) == ()
    assert repository.list_proposals(run.id) == ()
    assert repository.get_run(run.id).state is IngestionRunState.QUEUED
    assert result.lease_id is not None
    assert lease_repository.get_lease(result.lease_id).state is (
        IngestionRunLeaseState.EXPIRED
    )


def test_crash_recovery_resumes_after_successful_stage_without_reexecution() -> None:
    base = datetime(2026, 8, 2, 9, 0, tzinfo=UTC)
    plan = _plan(_stage("FIRST"), _stage("SECOND"))
    repository = InMemoryIngestionOrchestrationRepository()
    lease_repository = InMemoryIngestionRunLeaseRepository(repository)
    orchestration = IngestionOrchestrationService(repository)
    leases = IngestionRunLeaseService(lease_repository)
    first_processor = RecordingProcessor(marker="first")
    expiring_second = RecordingProcessor(
        marker="second-expired",
        before_return=lambda: leases.recover_expired(
            now=base + timedelta(seconds=6)
        ),
    )
    first_runner = IngestionWorkerRunner(
        repository=repository,
        orchestration=orchestration,
        leases=leases,
        registry=InMemoryIngestionWorkerRuntimeRegistry(
            (plan,),
            {
                _processor_key("FIRST"): first_processor,
                _processor_key("SECOND"): expiring_second,
            },
        ),
        observer=InMemoryIngestionWorkerObserver(),
        clock=lambda: base,
    )
    run = _start(orchestration)

    interrupted = first_runner.run_once(
        worker_ref="worker-one",
        pipeline_code=plan.pipeline_code,
        pipeline_version=plan.pipeline_version,
        ttl_seconds=5,
        trace_id="trace-first-claim",
    )
    assert interrupted.outcome is IngestionWorkerRunOutcome.LEASE_LOST
    assert len(repository.list_stage_executions(run.id)) == 1
    assert repository.get_run(run.id).state is IngestionRunState.QUEUED

    resumed_second = RecordingProcessor(marker="second-success")
    second_runner = IngestionWorkerRunner(
        repository=repository,
        orchestration=orchestration,
        leases=leases,
        registry=InMemoryIngestionWorkerRuntimeRegistry(
            (plan,),
            {
                _processor_key("FIRST"): first_processor,
                _processor_key("SECOND"): resumed_second,
            },
        ),
        observer=InMemoryIngestionWorkerObserver(),
        clock=lambda: base + timedelta(seconds=7),
    )
    resumed = second_runner.run_once(
        worker_ref="worker-two",
        pipeline_code=plan.pipeline_code,
        pipeline_version=plan.pipeline_version,
        ttl_seconds=60,
        trace_id="trace-second-claim",
    )

    assert resumed.outcome is IngestionWorkerRunOutcome.SUCCEEDED
    assert first_processor.inputs == [run.input_content_hash]
    assert first_processor.last_result is not None
    assert resumed_second.inputs == [first_processor.last_result.output_hash]
    assert len(repository.list_stage_executions(run.id)) == 2
    assert repository.get_run(run.id).state is IngestionRunState.SUCCEEDED


def test_retryable_and_final_failures_release_without_automatic_requeue() -> None:
    retry_plan = _plan(_stage("RETRY", attempts=2))
    retry_repository, retry_leases, retry_orchestration, _, _, retry_runner = _runtime(
        retry_plan,
        {_processor_key("RETRY"): RetryableProcessor()},
    )
    retry_run = _start(retry_orchestration)
    retry_result = retry_runner.run_once(
        worker_ref="worker-retry",
        pipeline_code=retry_plan.pipeline_code,
        pipeline_version=retry_plan.pipeline_version,
        ttl_seconds=60,
    )

    assert retry_result.outcome is IngestionWorkerRunOutcome.RETRYABLE_FAILURE
    assert retry_repository.get_run(retry_run.id).state is (
        IngestionRunState.FAILED_RETRYABLE
    )
    assert retry_result.lease_id is not None
    assert retry_leases.get_lease(retry_result.lease_id).state is (
        IngestionRunLeaseState.RELEASED
    )

    final_plan = _plan(_stage("FINAL"))
    final_repository, final_leases, final_orchestration, _, _, final_runner = _runtime(
        final_plan,
        {_processor_key("FINAL"): FinalProcessor()},
    )
    final_run = _start(final_orchestration)
    final_result = final_runner.run_once(
        worker_ref="worker-final",
        pipeline_code=final_plan.pipeline_code,
        pipeline_version=final_plan.pipeline_version,
        ttl_seconds=60,
    )

    assert final_result.outcome is IngestionWorkerRunOutcome.FINAL_FAILURE
    assert final_repository.get_run(final_run.id).state is IngestionRunState.FAILED_FINAL
    assert final_result.lease_id is not None
    assert final_leases.get_lease(final_result.lease_id).state is (
        IngestionRunLeaseState.RELEASED
    )


def test_empty_registry_blocks_without_claiming_work() -> None:
    repository = InMemoryIngestionOrchestrationRepository()
    lease_repository = InMemoryIngestionRunLeaseRepository(repository)
    orchestration = IngestionOrchestrationService(repository)
    run = _start(orchestration)
    observer = InMemoryIngestionWorkerObserver()
    runner = IngestionWorkerRunner(
        repository=repository,
        orchestration=orchestration,
        leases=IngestionRunLeaseService(lease_repository),
        registry=InMemoryIngestionWorkerRuntimeRegistry(),
        observer=observer,
    )

    result = runner.run_once(
        worker_ref="worker-empty",
        pipeline_code="TEST_PIPELINE",
        pipeline_version="1.0.0",
        ttl_seconds=60,
    )

    assert result.outcome is IngestionWorkerRunOutcome.BLOCKED
    assert result.error_code == "INGESTION_PIPELINE_NOT_REGISTERED"
    assert repository.get_run(run.id).state is IngestionRunState.QUEUED
    assert result.run_id is None and result.lease_id is None
    assert len(observer.results) == 1
