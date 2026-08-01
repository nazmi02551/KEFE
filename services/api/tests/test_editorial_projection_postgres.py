from __future__ import annotations

import os
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text

from kefe_api.infrastructure.postgres_editorial_projection import (
    PostgresEditorialProjectionRepository,
)
from kefe_api.modules.editorial_projection.in_memory import (
    InMemoryEditorialProjectionProfileRegistry,
    InMemoryReviewedProposalSource,
)
from kefe_api.modules.editorial_projection.models import (
    EditorialProjectionCommand,
    EditorialProjectionProfile,
    ReviewedProposal,
    ReviewedProposalBundle,
    stable_payload_hash,
)
from kefe_api.modules.editorial_projection.service import EditorialProjectionService

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)


def _proposal(kind: str, payload: dict, *, dependency_ids=()):
    return ReviewedProposal(
        id=uuid4(),
        proposal_kind=kind,
        payload_schema_ref=(
            "kefe.candidate-case" if kind == "CANDIDATE_CASE" else f"kefe.{kind.lower()}"
        ),
        payload_schema_version="1.0.0",
        payload=payload,
        payload_hash=stable_payload_hash(payload),
        review_decision_id=uuid4(),
        review_decision="ACCEPTED",
        dependency_ids=tuple(dependency_ids),
    )


def _service():
    decision_problem = _proposal("DECISION_PROBLEM", {"title": "Primary issue"})
    question = _proposal("QUESTION_DRAFT", {"prompt": "Choose?"})
    payload = {
        "slug": f"projection-{uuid4().hex[:10]}",
        "title": "Projected PostgreSQL Candidate Case",
        "summary": "Atomic DRAFT and projection lineage integration test.",
        "base_format_code": "DILEMMA",
        "primary_domain_code": "DAILY_LIFE",
        "content_risk": "L0",
        "issues": [
            {
                "code": "PRIMARY_ISSUE",
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
    candidate = _proposal(
        "CANDIDATE_CASE",
        payload,
        dependency_ids=(decision_problem.id, question.id),
    )
    bundle = ReviewedProposalBundle(
        candidate=candidate,
        dependencies=(decision_problem, question),
    )
    profile = EditorialProjectionProfile(
        profile_code="CANDIDATE_TO_AUTHORING",
        profile_version=1,
        candidate_schema_ref="kefe.candidate-case",
        candidate_schema_version="1.0.0",
        required_dependency_kinds=frozenset(
            {"DECISION_PROBLEM", "QUESTION_DRAFT"}
        ),
    )
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    repository = PostgresEditorialProjectionRepository(engine)
    service = EditorialProjectionService(
        InMemoryReviewedProposalSource((bundle,)),
        InMemoryEditorialProjectionProfileRegistry((profile,)),
        repository,
    )
    command = EditorialProjectionCommand(
        candidate_proposal_id=candidate.id,
        proposal_review_decision_id=candidate.review_decision_id,
        profile_code=profile.profile_code,
        profile_version=profile.profile_version,
        idempotency_key=f"projection-{uuid4()}",
        requested_by_admin_ref="admin:postgres-test",
    )
    return engine, service, command


def test_postgres_projection_atomically_creates_draft_and_lineage_only() -> None:
    engine, service, command = _service()

    first = service.project(command)
    replay = service.project(command)

    assert first.replayed is False
    assert replay.replayed is True
    assert replay.record == first.record

    with engine.connect() as connection:
        row = connection.execute(
            text(
                """
                SELECT pr.candidate_proposal_id, pr.input_hash,
                       cv.lifecycle_state, la.command
                FROM editorial.projection_record pr
                JOIN editorial.case_version cv
                  ON cv.id = pr.authoring_case_version_id
                JOIN editorial.lifecycle_audit la
                  ON la.case_version_id = cv.id
                WHERE pr.id = :record_id
                """
            ),
            {"record_id": first.record.id},
        ).mappings().one()
        projection_count = connection.execute(
            text(
                """
                SELECT count(*) FROM editorial.projection_record
                WHERE candidate_proposal_id = :candidate_id
                """
            ),
            {"candidate_id": command.candidate_proposal_id},
        ).scalar_one()
        consumer_count = connection.execute(
            text(
                """
                SELECT count(*) FROM content.case_version
                WHERE id = :version_id
                """
            ),
            {"version_id": first.record.authoring_case_version_id},
        ).scalar_one()

    assert row["candidate_proposal_id"] == command.candidate_proposal_id
    assert row["input_hash"] == first.record.input_hash
    assert row["lifecycle_state"] == "DRAFT"
    assert row["command"] == "project_candidate_case"
    assert projection_count == 1
    assert consumer_count == 0
