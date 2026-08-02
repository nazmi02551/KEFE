from __future__ import annotations

import os
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine, text

from kefe_api.infrastructure.postgres_editorial_projection import (
    PostgresEditorialProjectionRepository,
)
from kefe_api.infrastructure.postgres_ingestion_orchestration import (
    PostgresIngestionOrchestrationRepository,
)
from kefe_api.infrastructure.postgres_knowledge import PostgresKnowledgeRepository
from kefe_api.modules.editorial_projection.in_memory import (
    InMemoryEditorialProjectionProfileRegistry,
)
from kefe_api.modules.editorial_projection.ingestion_source import (
    IngestionReviewedProposalSource,
)
from kefe_api.modules.editorial_projection.models import (
    EditorialProjectionCommand,
    EditorialProjectionProfile,
)
from kefe_api.modules.editorial_projection.service import EditorialProjectionService
from kefe_api.modules.ingestion_orchestration.models import (
    ExecutorKind,
    InputArtifactKind,
    Proposal,
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


class FixedProcessor:
    def __init__(self, draft: ProposalDraft) -> None:
        self._draft = draft

    def process(self, **_) -> StageProcessorResult:
        return StageProcessorResult(proposals=(self._draft,))


def _add_proposal(
    service: IngestionOrchestrationService,
    repository: PostgresIngestionOrchestrationRepository,
    *,
    run_id: UUID,
    stage_code: str,
    draft: ProposalDraft,
) -> Proposal:
    before = {item.id for item in repository.list_proposals(run_id)}
    service.execute_stage(
        run_id=run_id,
        stage_code=stage_code,
        stage_version="1",
        input_hash=f"sha256:{stage_code.lower()}",
        max_attempts=1,
        executor_kind=ExecutorKind.DETERMINISTIC,
        processor=FixedProcessor(draft),
    )
    return next(
        item for item in repository.list_proposals(run_id) if item.id not in before
    )


def test_postgres_reviewed_proposals_project_atomically_into_authoring_draft() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    knowledge = PostgresKnowledgeRepository(engine)
    orchestration = PostgresIngestionOrchestrationRepository(engine)
    ingestion = IngestionOrchestrationService(orchestration)
    source_artifact = knowledge.add_source_artifact(
        SourceArtifact.create(
            adapter_code="projection-bridge-fixture",
            external_locator=f"https://example.test/bridge/{uuid4()}",
            content_hash=f"sha256:{uuid4().hex}",
            language_code="en",
        )
    )
    run = ingestion.start_run(
        input_artifact_kind=InputArtifactKind.SOURCE_ARTIFACT,
        input_artifact_id=source_artifact.id,
        input_content_hash=source_artifact.content_hash,
        pipeline_code="CANDIDATE_COMPOSITION",
        pipeline_version="1",
        configuration_hash="sha256:bridge-config",
        locale="en",
    )
    question = _add_proposal(
        ingestion,
        orchestration,
        run_id=run.id,
        stage_code="QUESTION_PROPOSAL",
        draft=ProposalDraft(
            proposal_kind="QUESTION_DRAFT",
            payload_schema_ref="kefe.question-draft",
            payload_schema_version="1.0.0",
            payload={"prompt": "Should children sit with a parent?"},
        ),
    )
    ingestion.review_proposal(
        proposal_id=question.id,
        decision=ProposalReviewDecisionKind.ACCEPTED,
        reviewer_ref="admin:question-reviewer",
    )
    candidate = _add_proposal(
        ingestion,
        orchestration,
        run_id=run.id,
        stage_code="CANDIDATE_CASE_COMPOSITION",
        draft=ProposalDraft(
            proposal_kind="CANDIDATE_CASE",
            payload_schema_ref="kefe.candidate-case",
            payload_schema_version="1.0.0",
            payload={
                "slug": f"postgres-bridge-{uuid4().hex[:8]}",
                "title": "Should children sit with a parent?",
                "summary": "A reviewed Candidate Case projected from PostgreSQL.",
                "base_format_code": "DILEMMA",
                "primary_domain_code": "TRAVEL",
                "content_risk": "L1",
                "content_locale": "en",
                "flow_template_code": "STANDARD_COMMIT_REVEAL",
                "flow_template_version_no": 1,
                "dependency_ids": [str(question.id)],
                "issues": [
                    {
                        "code": "PRIMARY_ISSUE",
                        "title": "Seat allocation",
                        "questions": [
                            {
                                "stable_code": "PRIMARY_DECISION",
                                "prompt": "Should children sit with a parent?",
                                "response_type": "SINGLE_CHOICE",
                                "response_schema": {"options": ["YES", "NO"]},
                            }
                        ],
                    }
                ],
            },
        ),
    )
    candidate_review = ingestion.review_proposal(
        proposal_id=candidate.id,
        decision=ProposalReviewDecisionKind.ACCEPTED,
        reviewer_ref="admin:candidate-reviewer",
    )
    profile = EditorialProjectionProfile(
        profile_code="INGESTION_CANDIDATE_TO_AUTHORING",
        profile_version=1,
        candidate_schema_ref="kefe.candidate-case",
        candidate_schema_version="1.0.0",
        required_dependency_kinds=frozenset({"QUESTION_DRAFT"}),
    )
    projection = EditorialProjectionService(
        IngestionReviewedProposalSource(orchestration),
        InMemoryEditorialProjectionProfileRegistry((profile,)),
        PostgresEditorialProjectionRepository(engine),
    )
    command = EditorialProjectionCommand(
        candidate_proposal_id=candidate.id,
        proposal_review_decision_id=candidate_review.id,
        profile_code=profile.profile_code,
        profile_version=profile.profile_version,
        idempotency_key="postgres-ingestion-bridge-attempt-1",
        requested_by_admin_ref="admin:projector",
    )

    first = projection.project(command)
    replay = projection.project(command)

    assert first.replayed is False
    assert replay.replayed is True
    with engine.connect() as connection:
        lifecycle_state = connection.execute(
            text(
                """
                SELECT lifecycle_state FROM editorial.case_version
                WHERE id = :version_id
                """
            ),
            {"version_id": first.record.authoring_case_version_id},
        ).scalar_one()
        projection_count = connection.execute(
            text(
                """
                SELECT count(*) FROM editorial.projection_record
                WHERE candidate_proposal_id = :candidate_id
                """
            ),
            {"candidate_id": candidate.id},
        ).scalar_one()

    assert lifecycle_state == "DRAFT"
    assert projection_count == 1
