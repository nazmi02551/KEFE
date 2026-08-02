from __future__ import annotations

import os
from dataclasses import dataclass
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text

from kefe_api.infrastructure.postgres_editorial_projection import (
    PostgresEditorialProjectionRepository,
)
from kefe_api.infrastructure.postgres_ingestion_orchestration import (
    PostgresIngestionOrchestrationRepository,
)
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
    ProposalDraft,
    ProposalReviewDecisionKind,
    StageProcessorResult,
)
from kefe_api.modules.ingestion_orchestration.service import (
    IngestionOrchestrationService,
)

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)


@dataclass
class StaticProcessor:
    drafts: tuple[ProposalDraft, ...]

    def process(self, **_kwargs) -> StageProcessorResult:
        return StageProcessorResult(proposals=self.drafts)


def test_postgres_reviewed_proposals_project_atomically_to_existing_authoring() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    ingestion_repository = PostgresIngestionOrchestrationRepository(engine)
    ingestion = IngestionOrchestrationService(ingestion_repository)
    run = ingestion.start_run(
        input_artifact_kind=InputArtifactKind.SOURCE_ARTIFACT,
        input_artifact_id=uuid4(),
        input_content_hash=f"source-{uuid4()}",
        pipeline_code="candidate-extraction",
        pipeline_version="1.0.0",
        configuration_hash="config-v1",
        methodology_version="method-v1",
        locale="en",
    )
    ingestion.execute_stage(
        run_id=run.id,
        stage_code="extract-dependencies",
        stage_version="1.0.0",
        input_hash="dependency-input",
        max_attempts=1,
        executor_kind=ExecutorKind.DETERMINISTIC,
        processor=StaticProcessor(
            (
                ProposalDraft(
                    proposal_kind="DECISION_PROBLEM",
                    payload_schema_ref="kefe.decision_problem",
                    payload_schema_version="1.0.0",
                    payload={"title": "Primary issue"},
                ),
                ProposalDraft(
                    proposal_kind="QUESTION_DRAFT",
                    payload_schema_ref="kefe.question_draft",
                    payload_schema_version="1.0.0",
                    payload={"prompt": "Choose?"},
                ),
            )
        ),
    )
    dependencies = ingestion_repository.list_proposals(run.id)
    candidate_payload = {
        "slug": f"postgres-reviewed-{uuid4().hex[:8]}",
        "title": "PostgreSQL reviewed Candidate Case",
        "summary": "Durable Proposal review projected into existing authoring.",
        "base_format_code": "DILEMMA",
        "primary_domain_code": "DAILY_LIFE",
        "content_risk": "L0",
        "dependency_proposal_ids": [str(item.id) for item in dependencies],
        "issues": [
            {
                "code": "PRIMARY",
                "title": "Primary issue",
                "questions": [
                    {
                        "stable_code": "PRIMARY_DECISION",
                        "prompt": "Choose?",
                        "response_type": "SINGLE_CHOICE",
                        "response_schema": {"options": ["A", "B"]},
                    }
                ],
            }
        ],
        "flow_template_code": "STANDARD_COMMIT_REVEAL",
        "flow_template_version_no": 1,
    }
    ingestion.execute_stage(
        run_id=run.id,
        stage_code="compose-candidate",
        stage_version="1.0.0",
        input_hash="candidate-input",
        max_attempts=1,
        executor_kind=ExecutorKind.DETERMINISTIC,
        processor=StaticProcessor(
            (
                ProposalDraft(
                    proposal_kind="CANDIDATE_CASE",
                    payload_schema_ref="kefe.candidate-case",
                    payload_schema_version="1.0.0",
                    payload=candidate_payload,
                ),
            )
        ),
    )
    proposals = ingestion_repository.list_proposals(run.id)
    candidate = next(item for item in proposals if item.proposal_kind == "CANDIDATE_CASE")
    reviews = {
        proposal.id: ingestion.review_proposal(
            proposal_id=proposal.id,
            decision=ProposalReviewDecisionKind.ACCEPTED,
            reviewer_ref=f"reviewer:{proposal.id}",
        )
        for proposal in proposals
    }
    ingestion.mark_succeeded(run.id)

    projection = EditorialProjectionService(
        IngestionReviewedProposalSource(ingestion_repository),
        InMemoryEditorialProjectionProfileRegistry(
            (
                EditorialProjectionProfile(
                    profile_code="CANDIDATE_TO_AUTHORING",
                    profile_version=1,
                    candidate_schema_ref="kefe.candidate-case",
                    candidate_schema_version="1.0.0",
                    required_dependency_kinds=frozenset(
                        {"DECISION_PROBLEM", "QUESTION_DRAFT"}
                    ),
                ),
            )
        ),
        PostgresEditorialProjectionRepository(engine),
    )
    command = EditorialProjectionCommand(
        candidate_proposal_id=candidate.id,
        proposal_review_decision_id=reviews[candidate.id].id,
        profile_code="CANDIDATE_TO_AUTHORING",
        profile_version=1,
        idempotency_key=f"projection-{uuid4()}",
        requested_by_admin_ref="admin:postgres-reviewed-source-test",
    )

    first = projection.project(command)
    replay = projection.project(command)

    assert first.replayed is False
    assert replay.replayed is True
    assert replay.record == first.record
    with engine.connect() as connection:
        row = connection.execute(
            text(
                """
                SELECT r.state, p.proposal_kind, d.decision,
                       cv.lifecycle_state, pr.requested_by_admin_ref
                FROM ingestion.ingestion_run r
                JOIN ingestion.proposal p ON p.run_id = r.id
                JOIN ingestion.proposal_review_decision d ON d.proposal_id = p.id
                JOIN editorial.projection_record pr
                  ON pr.candidate_proposal_id = p.id
                JOIN editorial.case_version cv
                  ON cv.id = pr.authoring_case_version_id
                WHERE r.id = :run_id AND p.id = :candidate_id
                """
            ),
            {"run_id": run.id, "candidate_id": candidate.id},
        ).mappings().one()
        consumer_count = connection.execute(
            text(
                """
                SELECT count(*) FROM content.case_version
                WHERE id = :version_id
                """
            ),
            {"version_id": first.record.authoring_case_version_id},
        ).scalar_one()

    assert row["state"] == "SUCCEEDED"
    assert row["proposal_kind"] == "CANDIDATE_CASE"
    assert row["decision"] == "ACCEPTED"
    assert row["lifecycle_state"] == "DRAFT"
    assert row["requested_by_admin_ref"] == command.requested_by_admin_ref
    assert consumer_count == 0
