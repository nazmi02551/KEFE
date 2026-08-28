from __future__ import annotations

from uuid import uuid4

import pytest

from kefe_api.modules.ingestion_orchestration.in_memory import (
    InMemoryIngestionOrchestrationRepository,
)
from kefe_api.modules.ingestion_orchestration.knowledge_materializer import (
    KnowledgeProposalMaterializer,
)
from kefe_api.modules.ingestion_orchestration.models import (
    ExecutorKind,
    IngestionRunState,
    InputArtifactKind,
    ProposalDraft,
    ProposalReviewDecisionKind,
    StageOutcome,
    StageProcessorResult,
)
from kefe_api.modules.ingestion_orchestration.service import (
    IngestionOrchestrationService,
    RetryableStageError,
)
from kefe_api.modules.knowledge.in_memory import InMemoryKnowledgeRepository
from kefe_api.modules.knowledge.models import ClaimState, ClaimType


class FixedProcessor:
    def __init__(self, *proposals: ProposalDraft) -> None:
        self._proposals = proposals

    def process(self, **_) -> StageProcessorResult:
        return StageProcessorResult(
            proposals=tuple(self._proposals),
            output_metadata={"processor": "fixture"},
        )


class RetryableFailureProcessor:
    def process(self, **_) -> StageProcessorResult:
        raise RetryableStageError("FIXTURE_RETRYABLE")


def _service() -> tuple[
    IngestionOrchestrationService,
    InMemoryIngestionOrchestrationRepository,
]:
    repository = InMemoryIngestionOrchestrationRepository()
    return IngestionOrchestrationService(repository), repository


def _start_run(service: IngestionOrchestrationService):
    return service.start_run(
        input_artifact_kind=InputArtifactKind.SOURCE_ARTIFACT,
        input_artifact_id=uuid4(),
        input_content_hash="sha256:source-v1",
        pipeline_code="TODAY_RADAR",
        pipeline_version="1",
        configuration_hash="sha256:config-v1",
        taxonomy_version="claims-v1",
        locale="tr-TR",
        jurisdiction_code="TR",
    )


def test_run_identity_is_replay_safe_and_versions_create_new_runs() -> None:
    service, _ = _service()
    artifact_id = uuid4()
    first = service.start_run(
        input_artifact_kind=InputArtifactKind.SOURCE_ARTIFACT,
        input_artifact_id=artifact_id,
        input_content_hash="sha256:one",
        pipeline_code="RADAR",
        pipeline_version="1",
        configuration_hash="sha256:config",
    )
    replay = service.start_run(
        input_artifact_kind=InputArtifactKind.SOURCE_ARTIFACT,
        input_artifact_id=artifact_id,
        input_content_hash="sha256:one",
        pipeline_code="RADAR",
        pipeline_version="1",
        configuration_hash="sha256:config",
    )
    changed_version = service.start_run(
        input_artifact_kind=InputArtifactKind.SOURCE_ARTIFACT,
        input_artifact_id=artifact_id,
        input_content_hash="sha256:one",
        pipeline_code="RADAR",
        pipeline_version="2",
        configuration_hash="sha256:config",
    )

    assert replay.id == first.id
    assert changed_version.id != first.id


def test_stage_retry_is_bounded_and_run_becomes_final_after_limit() -> None:
    service, repository = _service()
    run = _start_run(service)

    first = service.execute_stage(
        run_id=run.id,
        stage_code="CLAIM_EXTRACTION",
        stage_version="1",
        input_hash="sha256:normalized",
        max_attempts=2,
        executor_kind=ExecutorKind.DETERMINISTIC,
        processor=RetryableFailureProcessor(),
    )
    assert first.outcome is StageOutcome.FAILED_RETRYABLE
    assert repository.get_run(run.id).state is IngestionRunState.FAILED_RETRYABLE

    service.requeue(run.id)
    second = service.execute_stage(
        run_id=run.id,
        stage_code="CLAIM_EXTRACTION",
        stage_version="1",
        input_hash="sha256:normalized",
        max_attempts=2,
        executor_kind=ExecutorKind.DETERMINISTIC,
        processor=RetryableFailureProcessor(),
    )

    assert second.attempt_no == 2
    assert second.outcome is StageOutcome.FAILED_FINAL
    assert repository.get_run(run.id).state is IngestionRunState.FAILED_FINAL
    with pytest.raises(ValueError, match="not executable"):
        service.execute_stage(
            run_id=run.id,
            stage_code="CLAIM_EXTRACTION",
            stage_version="1",
            input_hash="sha256:normalized",
            max_attempts=3,
            executor_kind=ExecutorKind.DETERMINISTIC,
            processor=FixedProcessor(),
        )


def test_processor_creates_unreviewed_proposal_and_review_is_terminal() -> None:
    service, repository = _service()
    run = _start_run(service)
    execution = service.execute_stage(
        run_id=run.id,
        stage_code="CLAIM_EXTRACTION",
        stage_version="1",
        input_hash="sha256:normalized",
        max_attempts=1,
        executor_kind=ExecutorKind.AI_ASSISTED,
        processor=FixedProcessor(
            ProposalDraft(
                proposal_kind="CLAIM",
                payload_schema_ref="knowledge/claim",
                payload_schema_version="1",
                payload={"normalized_text": "Örnek iddia", "language_code": "tr"},
                confidence=0.73,
                ai_execution_ref="ai-execution:fixture",
            )
        ),
    )
    assert execution.outcome is StageOutcome.SUCCEEDED
    proposal = repository.list_proposals(run.id)[0]
    assert proposal.ai_execution_ref == "ai-execution:fixture"
    assert repository.get_review_decision(proposal.id) is None

    review = service.review_proposal(
        proposal_id=proposal.id,
        decision=ProposalReviewDecisionKind.ACCEPTED,
        reviewer_ref="admin:editor:fixture",
    )
    assert review.decision is ProposalReviewDecisionKind.ACCEPTED
    with pytest.raises(ValueError, match="terminal review"):
        service.review_proposal(
            proposal_id=proposal.id,
            decision=ProposalReviewDecisionKind.REJECTED,
            reviewer_ref="admin:editor:second",
        )


def test_accepted_claim_materialization_is_idempotent() -> None:
    service, repository = _service()
    knowledge = InMemoryKnowledgeRepository()
    run = _start_run(service)
    service.execute_stage(
        run_id=run.id,
        stage_code="CLAIM_EXTRACTION",
        stage_version="1",
        input_hash="sha256:normalized",
        max_attempts=1,
        executor_kind=ExecutorKind.DETERMINISTIC,
        processor=FixedProcessor(
            ProposalDraft(
                proposal_kind="CLAIM",
                payload_schema_ref="knowledge/claim",
                payload_schema_version="1",
                payload={"normalized_text": "Kalıcı iddia", "language_code": "tr"},
                provenance_ref="run:fixture:claim",
            )
        ),
    )
    proposal = repository.list_proposals(run.id)[0]
    service.review_proposal(
        proposal_id=proposal.id,
        decision=ProposalReviewDecisionKind.ACCEPTED,
        reviewer_ref="admin:editor:fixture",
    )
    materializer = KnowledgeProposalMaterializer(
        knowledge_repository=knowledge,
        orchestration_repository=repository,
    )

    first = service.materialize_accepted_proposal(
        proposal_id=proposal.id,
        materializer=materializer,
    )
    replay = service.materialize_accepted_proposal(
        proposal_id=proposal.id,
        materializer=materializer,
    )

    assert replay == first
    claim = knowledge.get_claim(first.target_id)
    assert claim is not None
    assert claim.normalized_text == "Kalıcı iddia"


def test_claim_assessment_can_reference_a_materialized_claim_proposal() -> None:
    service, repository = _service()
    knowledge = InMemoryKnowledgeRepository()
    materializer = KnowledgeProposalMaterializer(
        knowledge_repository=knowledge,
        orchestration_repository=repository,
    )
    run = _start_run(service)

    service.execute_stage(
        run_id=run.id,
        stage_code="CLAIM_EXTRACTION",
        stage_version="1",
        input_hash="sha256:normalized",
        max_attempts=1,
        executor_kind=ExecutorKind.DETERMINISTIC,
        processor=FixedProcessor(
            ProposalDraft(
                proposal_kind="CLAIM",
                payload_schema_ref="knowledge/claim",
                payload_schema_version="1",
                payload={"normalized_text": "Değerlendirilecek iddia", "language_code": "tr"},
            )
        ),
    )
    claim_proposal = repository.list_proposals(run.id)[0]
    service.review_proposal(
        proposal_id=claim_proposal.id,
        decision=ProposalReviewDecisionKind.ACCEPTED,
        reviewer_ref="admin:editor:fixture",
    )
    claim_materialization = service.materialize_accepted_proposal(
        proposal_id=claim_proposal.id,
        materializer=materializer,
    )

    service.execute_stage(
        run_id=run.id,
        stage_code="FACT_CHECK_ASSIST",
        stage_version="1",
        input_hash="sha256:claim",
        max_attempts=1,
        executor_kind=ExecutorKind.DETERMINISTIC,
        processor=FixedProcessor(
            ProposalDraft(
                proposal_kind="CLAIM_ASSESSMENT",
                payload_schema_ref="knowledge/claim-assessment",
                payload_schema_version="1",
                payload={
                    "claim_proposal_id": str(claim_proposal.id),
                    "claim_type": ClaimType.FACTUAL.value,
                    "claim_state": ClaimState.SUPPORTED.value,
                    "taxonomy_version": "claims-v1",
                },
            )
        ),
    )
    assessment_proposal = repository.list_proposals(run.id)[1]
    review = service.review_proposal(
        proposal_id=assessment_proposal.id,
        decision=ProposalReviewDecisionKind.ACCEPTED,
        reviewer_ref="admin:reviewer:fixture",
    )
    service.materialize_accepted_proposal(
        proposal_id=assessment_proposal.id,
        materializer=materializer,
    )

    assessments = knowledge.list_claim_assessments(claim_materialization.target_id)
    assert len(assessments) == 1
    assert assessments[0].claim_state is ClaimState.SUPPORTED
    assert assessments[0].reviewer_ref == review.reviewer_ref


def test_rejected_proposal_cannot_materialize() -> None:
    service, repository = _service()
    knowledge = InMemoryKnowledgeRepository()
    run = _start_run(service)
    service.execute_stage(
        run_id=run.id,
        stage_code="CLAIM_EXTRACTION",
        stage_version="1",
        input_hash="sha256:normalized",
        max_attempts=1,
        executor_kind=ExecutorKind.DETERMINISTIC,
        processor=FixedProcessor(
            ProposalDraft(
                proposal_kind="CLAIM",
                payload_schema_ref="knowledge/claim",
                payload_schema_version="1",
                payload={"normalized_text": "Reddedilen", "language_code": "tr"},
            )
        ),
    )
    proposal = repository.list_proposals(run.id)[0]
    service.review_proposal(
        proposal_id=proposal.id,
        decision=ProposalReviewDecisionKind.REJECTED,
        reviewer_ref="admin:editor:fixture",
    )

    with pytest.raises(ValueError, match="ACCEPTED"):
        service.materialize_accepted_proposal(
            proposal_id=proposal.id,
            materializer=KnowledgeProposalMaterializer(
                knowledge_repository=knowledge,
                orchestration_repository=repository,
            ),
        )
