from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from kefe_api.modules.ingestion_orchestration.in_memory import (
    InMemoryIngestionOrchestrationRepository,
)
from kefe_api.modules.ingestion_orchestration.models import (
    ExecutorKind,
    IngestionRunState,
    InputArtifactKind,
    Proposal,
    ProposalDraft,
    StageExecution,
    StageOutcome,
    StageProcessorResult,
    stable_payload_hash,
    utcnow,
)
from kefe_api.modules.ingestion_orchestration.service import (
    IngestionOrchestrationService,
)


class AtomicOnlyRepository(InMemoryIngestionOrchestrationRepository):
    def __init__(self) -> None:
        super().__init__()
        self.successful_batch_calls = 0

    def add_stage_execution(self, execution: StageExecution) -> None:
        raise AssertionError("successful service path must not persist stage separately")

    def add_proposal(self, proposal: Proposal) -> None:
        raise AssertionError("successful service path must not persist Proposal separately")

    def complete_successful_stage(
        self,
        execution: StageExecution,
        proposals: tuple[Proposal, ...],
    ) -> None:
        self.successful_batch_calls += 1
        super().complete_successful_stage(execution, proposals)


class TwoProposalProcessor:
    def process(self, **_) -> StageProcessorResult:
        return StageProcessorResult(
            proposals=(
                ProposalDraft(
                    proposal_kind="DECISION_PROBLEM",
                    payload_schema_ref="kefe.decision-problem",
                    payload_schema_version="1.0.0",
                    payload={"title": "Atomic issue"},
                ),
                ProposalDraft(
                    proposal_kind="QUESTION_DRAFT",
                    payload_schema_ref="kefe.question-draft",
                    payload_schema_version="1.0.0",
                    payload={"prompt": "Atomic question?"},
                ),
            ),
            output_metadata={"batch": "atomic"},
        )


def _running_repository() -> tuple[
    InMemoryIngestionOrchestrationRepository,
    UUID,
]:
    repository = InMemoryIngestionOrchestrationRepository()
    service = IngestionOrchestrationService(repository)
    run = service.start_run(
        input_artifact_kind=InputArtifactKind.SOURCE_ARTIFACT,
        input_artifact_id=uuid4(),
        input_content_hash=f"sha256:{uuid4()}",
        pipeline_code="ATOMIC_BATCH",
        pipeline_version="1",
        configuration_hash="sha256:atomic-config",
    )
    repository.update_run(run.transition(IngestionRunState.RUNNING))
    return repository, run.id


def _execution(run_id: UUID, *, stage_code: str = "ATOMIC_STAGE") -> StageExecution:
    now = utcnow()
    return StageExecution(
        id=uuid4(),
        run_id=run_id,
        stage_code=stage_code,
        stage_version="1",
        attempt_no=1,
        max_attempts=1,
        executor_kind=ExecutorKind.DETERMINISTIC,
        input_hash=f"sha256:{stage_code.lower()}",
        output_hash=f"sha256:{stage_code.lower()}:output",
        started_at=now,
        completed_at=now,
        outcome=StageOutcome.SUCCEEDED,
    )


def _proposal(
    execution: StageExecution,
    proposal_id: UUID,
    *,
    supersedes: UUID | None = None,
) -> Proposal:
    payload = {"proposal_id": str(proposal_id)}
    return Proposal(
        id=proposal_id,
        proposal_kind="QUESTION_DRAFT",
        payload_schema_ref="kefe.question-draft",
        payload_schema_version="1.0.0",
        payload=payload,
        payload_hash=stable_payload_hash(payload),
        run_id=execution.run_id,
        stage_execution_id=execution.id,
        created_at=execution.completed_at or utcnow(),
        supersedes_proposal_id=supersedes,
    )


def test_service_uses_one_atomic_success_repository_call() -> None:
    repository = AtomicOnlyRepository()
    service = IngestionOrchestrationService(repository)
    run = service.start_run(
        input_artifact_kind=InputArtifactKind.SOURCE_ARTIFACT,
        input_artifact_id=uuid4(),
        input_content_hash="sha256:service-atomic-source",
        pipeline_code="ATOMIC_SERVICE",
        pipeline_version="1",
        configuration_hash="sha256:service-atomic-config",
    )

    execution = service.execute_stage(
        run_id=run.id,
        stage_code="COMPOSE",
        stage_version="1",
        input_hash="sha256:service-input",
        max_attempts=1,
        executor_kind=ExecutorKind.DETERMINISTIC,
        processor=TwoProposalProcessor(),
    )

    assert execution.outcome is StageOutcome.SUCCEEDED
    assert repository.successful_batch_calls == 1
    assert repository.list_stage_executions(run.id) == (execution,)
    assert len(repository.list_proposals(run.id)) == 2


def test_memory_invalid_batch_rolls_back_stage_and_all_proposals() -> None:
    repository, run_id = _running_repository()
    execution = _execution(run_id)
    first = _proposal(execution, uuid4())
    invalid = _proposal(execution, uuid4(), supersedes=uuid4())

    with pytest.raises(KeyError):
        repository.complete_successful_stage(execution, (first, invalid))

    assert repository.list_stage_executions(run_id) == ()
    assert repository.list_proposals(run_id) == ()
    assert repository.get_run(run_id).state is IngestionRunState.RUNNING


def test_memory_orders_same_batch_supersession_and_rejects_cycles() -> None:
    repository, run_id = _running_repository()
    execution = _execution(run_id, stage_code="ORDERED_STAGE")
    parent_id = uuid4()
    child_id = uuid4()
    parent = _proposal(execution, parent_id)
    child = _proposal(execution, child_id, supersedes=parent_id)

    repository.complete_successful_stage(execution, (child, parent))

    assert repository.get_proposal(parent_id) == parent
    assert repository.get_proposal(child_id) == child
    assert repository.list_stage_executions(run_id) == (execution,)

    cycle_execution = _execution(run_id, stage_code="CYCLE_STAGE")
    first_id = uuid4()
    second_id = uuid4()
    first = _proposal(cycle_execution, first_id, supersedes=second_id)
    second = _proposal(cycle_execution, second_id, supersedes=first_id)

    with pytest.raises(ValueError, match="cycle"):
        repository.complete_successful_stage(cycle_execution, (first, second))

    assert repository.list_stage_executions(run_id) == (execution,)
    assert len(repository.list_proposals(run_id)) == 2
