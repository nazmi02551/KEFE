from __future__ import annotations

import os
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text

from kefe_api.infrastructure.postgres_ingestion_orchestration import (
    PostgresIngestionOrchestrationRepository,
)
from kefe_api.infrastructure.postgres_knowledge import PostgresKnowledgeRepository
from kefe_api.modules.ingestion_orchestration.knowledge_materializer import (
    KnowledgeProposalMaterializer,
)
from kefe_api.modules.ingestion_orchestration.models import (
    ExecutorKind,
    IngestionRunState,
    InputArtifactKind,
    Proposal,
    ProposalDraft,
    ProposalReviewDecisionKind,
    StageExecution,
    StageOutcome,
    StageProcessorResult,
    stable_payload_hash,
    utcnow,
)
from kefe_api.modules.ingestion_orchestration.service import (
    IngestionOrchestrationService,
)
from kefe_api.modules.knowledge.models import SourceArtifact

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)


class FixedClaimProcessor:
    def process(self, **_) -> StageProcessorResult:
        return StageProcessorResult(
            proposals=(
                ProposalDraft(
                    proposal_kind="CLAIM",
                    payload_schema_ref="knowledge/claim",
                    payload_schema_version="1",
                    payload={
                        "normalized_text": "PostgreSQL orchestration iddiası",
                        "language_code": "tr",
                    },
                    provenance_ref="postgres:orchestration:fixture",
                ),
            ),
            output_metadata={"fixture": True},
        )


def test_postgres_orchestration_replay_review_and_materialization() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    knowledge = PostgresKnowledgeRepository(engine)
    orchestration = PostgresIngestionOrchestrationRepository(engine)
    service = IngestionOrchestrationService(orchestration)

    source = knowledge.add_source_artifact(
        SourceArtifact.create(
            adapter_code="ingestion-postgres-fixture",
            external_locator=f"https://example.test/orchestration/{uuid4()}",
            content_hash="sha256:orchestration-source-v1",
            language_code="tr",
        )
    )

    run = service.start_run(
        input_artifact_kind=InputArtifactKind.SOURCE_ARTIFACT,
        input_artifact_id=source.id,
        input_content_hash=source.content_hash,
        pipeline_code="TODAY_RADAR",
        pipeline_version="1",
        configuration_hash="sha256:orchestration-config-v1",
        taxonomy_version="claims-v1",
        locale="tr-TR",
        jurisdiction_code="TR",
    )
    replay = service.start_run(
        input_artifact_kind=InputArtifactKind.SOURCE_ARTIFACT,
        input_artifact_id=source.id,
        input_content_hash=source.content_hash,
        pipeline_code="TODAY_RADAR",
        pipeline_version="1",
        configuration_hash="sha256:orchestration-config-v1",
        taxonomy_version="claims-v1",
        locale="tr-TR",
        jurisdiction_code="TR",
    )
    assert replay.id == run.id

    service.execute_stage(
        run_id=run.id,
        stage_code="CLAIM_EXTRACTION",
        stage_version="1",
        input_hash="sha256:normalized-input-v1",
        max_attempts=2,
        executor_kind=ExecutorKind.DETERMINISTIC,
        processor=FixedClaimProcessor(),
        trace_id="trace:postgres-orchestration",
    )
    proposal = orchestration.list_proposals(run.id)[0]
    review = service.review_proposal(
        proposal_id=proposal.id,
        decision=ProposalReviewDecisionKind.ACCEPTED,
        reviewer_ref="admin:postgres-reviewer",
        policy_version="review-policy-v1",
    )

    materializer = KnowledgeProposalMaterializer(
        knowledge_repository=knowledge,
        orchestration_repository=orchestration,
    )
    first = service.materialize_accepted_proposal(
        proposal_id=proposal.id,
        materializer=materializer,
    )
    second = service.materialize_accepted_proposal(
        proposal_id=proposal.id,
        materializer=materializer,
    )

    assert second == first
    claim = knowledge.get_claim(first.target_id)
    assert claim is not None
    assert claim.normalized_text == "PostgreSQL orchestration iddiası"
    assert orchestration.get_review_decision(proposal.id) == review

    with pytest.raises(ValueError, match="ingestion persistence invariant"):
        service.review_proposal(
            proposal_id=proposal.id,
            decision=ProposalReviewDecisionKind.REJECTED,
            reviewer_ref="admin:other-reviewer",
        )

    with engine.connect() as connection:
        run_count = connection.execute(
            text(
                """
                SELECT count(*) FROM ingestion.ingestion_run
                WHERE run_key = :run_key
                """
            ),
            {"run_key": run.run_key},
        ).scalar_one()
        materialization_count = connection.execute(
            text(
                """
                SELECT count(*) FROM ingestion.proposal_materialization
                WHERE proposal_id = :proposal_id AND target_kind = 'CLAIM'
                """
            ),
            {"proposal_id": proposal.id},
        ).scalar_one()

    assert run_count == 1
    assert materialization_count == 1


def test_postgres_success_stage_batch_rolls_back_and_orders_supersession() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    knowledge = PostgresKnowledgeRepository(engine)
    orchestration = PostgresIngestionOrchestrationRepository(engine)
    service = IngestionOrchestrationService(orchestration)
    source = knowledge.add_source_artifact(
        SourceArtifact.create(
            adapter_code="atomic-stage-batch-fixture",
            external_locator=f"https://example.test/atomic-stage/{uuid4()}",
            content_hash=f"sha256:atomic-stage-{uuid4()}",
            language_code="en",
        )
    )
    run = service.start_run(
        input_artifact_kind=InputArtifactKind.SOURCE_ARTIFACT,
        input_artifact_id=source.id,
        input_content_hash=source.content_hash,
        pipeline_code="ATOMIC_STAGE_BATCH",
        pipeline_version="1",
        configuration_hash="sha256:atomic-stage-config",
    )
    orchestration.update_run(run.transition(IngestionRunState.RUNNING))

    now = utcnow()
    execution = StageExecution(
        id=uuid4(),
        run_id=run.id,
        stage_code="COMPOSE",
        stage_version="1",
        attempt_no=1,
        max_attempts=1,
        executor_kind=ExecutorKind.DETERMINISTIC,
        input_hash="sha256:atomic-stage-input",
        output_hash="sha256:atomic-stage-output",
        started_at=now,
        completed_at=now,
        outcome=StageOutcome.SUCCEEDED,
    )

    def proposal(proposal_id, *, supersedes=None) -> Proposal:
        payload = {"proposal_id": str(proposal_id)}
        return Proposal(
            id=proposal_id,
            proposal_kind="QUESTION_DRAFT",
            payload_schema_ref="kefe.question-draft",
            payload_schema_version="1.0.0",
            payload=payload,
            payload_hash=stable_payload_hash(payload),
            run_id=run.id,
            stage_execution_id=execution.id,
            created_at=now,
            supersedes_proposal_id=supersedes,
        )

    invalid_parent = proposal(uuid4())
    invalid_child = proposal(uuid4(), supersedes=uuid4())
    with pytest.raises(KeyError):
        orchestration.complete_successful_stage(
            execution,
            (invalid_parent, invalid_child),
        )

    with engine.connect() as connection:
        failed_stage_count = connection.execute(
            text(
                """
                SELECT count(*) FROM ingestion.stage_execution
                WHERE id = :execution_id
                """
            ),
            {"execution_id": execution.id},
        ).scalar_one()
        failed_proposal_count = connection.execute(
            text(
                """
                SELECT count(*) FROM ingestion.proposal
                WHERE stage_execution_id = :execution_id
                """
            ),
            {"execution_id": execution.id},
        ).scalar_one()
    assert failed_stage_count == 0
    assert failed_proposal_count == 0

    parent_id = uuid4()
    child_id = uuid4()
    parent = proposal(parent_id)
    child = proposal(child_id, supersedes=parent_id)
    orchestration.complete_successful_stage(execution, (child, parent))

    stored = {item.id: item for item in orchestration.list_proposals(run.id)}
    assert stored[parent_id] == parent
    assert stored[child_id] == child
    assert orchestration.list_stage_executions(run.id) == (execution,)

    with engine.connect() as connection:
        success_stage_count = connection.execute(
            text(
                """
                SELECT count(*) FROM ingestion.stage_execution
                WHERE id = :execution_id
                """
            ),
            {"execution_id": execution.id},
        ).scalar_one()
        success_proposal_count = connection.execute(
            text(
                """
                SELECT count(*) FROM ingestion.proposal
                WHERE stage_execution_id = :execution_id
                """
            ),
            {"execution_id": execution.id},
        ).scalar_one()
    assert success_stage_count == 1
    assert success_proposal_count == 2
