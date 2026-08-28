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
    InputArtifactKind,
    ProposalDraft,
    ProposalReviewDecisionKind,
    StageProcessorResult,
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
