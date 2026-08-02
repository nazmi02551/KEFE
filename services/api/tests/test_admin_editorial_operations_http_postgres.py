from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from kefe_api.core.settings import get_settings
from kefe_api.main import create_app
from kefe_api.modules.admin_security.router import ADMIN_CSRF_HEADER, ADMIN_SESSION_COOKIE
from kefe_api.modules.ingestion_orchestration.models import (
    ExecutorKind,
    InputArtifactKind,
    Proposal,
    ProposalDraft,
    StageProcessorResult,
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


def _seed_subject(database_url: str, role: str) -> UUID:
    subject_id = uuid4()
    now = datetime.now(UTC)
    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO admin_security.subject (id, state)
                VALUES (:subject_id, 'ACTIVE')
                """
            ),
            {"subject_id": subject_id},
        )
        connection.execute(
            text(
                """
                INSERT INTO admin_security.role_assignment (
                    id, subject_id, role, granted_at
                ) VALUES (:id, :subject_id, :role, :granted_at)
                """
            ),
            {
                "id": uuid4(),
                "subject_id": subject_id,
                "role": role,
                "granted_at": now,
            },
        )
    return subject_id


def _admin_client(app, subject_id: UUID) -> tuple[TestClient, str]:
    now = datetime.now(UTC)
    issued = app.state.admin_session_store.issue(
        admin_subject_id=subject_id,
        authenticated_at=now,
        mfa_satisfied_at=now,
        expires_at=now + timedelta(hours=12),
    )
    client = TestClient(app)
    client.cookies.set(ADMIN_SESSION_COOKIE, issued.session_token)
    return client, issued.csrf_token


def _seed_candidate(app) -> tuple[tuple[Proposal, ...], Proposal]:
    service = app.state.ingestion_orchestration_service
    repository = app.state.ingestion_orchestration_repository
    run = service.start_run(
        input_artifact_kind=InputArtifactKind.SOURCE_ARTIFACT,
        input_artifact_id=uuid4(),
        input_content_hash=f"admin-operations-pg-{uuid4()}",
        pipeline_code="candidate-extraction",
        pipeline_version="1.0.0",
        configuration_hash="config-v1",
        methodology_version="method-v1",
        locale="en",
    )
    service.execute_stage(
        run_id=run.id,
        stage_code="extract-dependencies",
        stage_version="1.0.0",
        input_hash="dependencies",
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
    dependencies = repository.list_proposals(run.id)
    service.execute_stage(
        run_id=run.id,
        stage_code="compose-candidate",
        stage_version="1.0.0",
        input_hash="candidate",
        max_attempts=1,
        executor_kind=ExecutorKind.DETERMINISTIC,
        processor=StaticProcessor(
            (
                ProposalDraft(
                    proposal_kind="CANDIDATE_CASE",
                    payload_schema_ref="kefe.candidate-case",
                    payload_schema_version="1.0.0",
                    payload={
                        "slug": f"admin-operations-pg-{uuid4().hex[:8]}",
                        "title": "PostgreSQL Admin operations",
                        "summary": "Secured review and explicit projection.",
                        "base_format_code": "DILEMMA",
                        "primary_domain_code": "DAILY_LIFE",
                        "content_risk": "L0",
                        "dependency_proposal_ids": [
                            str(item.id) for item in dependencies
                        ],
                        "issues": [
                            {
                                "code": "PRIMARY",
                                "title": "Primary issue",
                                "questions": [
                                    {
                                        "stable_code": "PRIMARY_DECISION",
                                        "prompt": "Choose?",
                                        "response_type": "SINGLE_CHOICE",
                                        "response_schema": {
                                            "options": ["A", "B"]
                                        },
                                    }
                                ],
                            }
                        ],
                        "flow_template_code": "STANDARD_COMMIT_REVEAL",
                        "flow_template_version_no": 1,
                    },
                ),
            )
        ),
    )
    service.mark_succeeded(run.id)
    proposals = repository.list_proposals(run.id)
    candidate = next(
        proposal for proposal in proposals if proposal.proposal_kind == "CANDIDATE_CASE"
    )
    return proposals, candidate


def test_postgres_admin_review_then_explicit_projection_is_audited_and_bounded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = os.environ["KEFE_DATABASE_URL"]
    monkeypatch.setenv("KEFE_PERSISTENCE_BACKEND", "postgres")
    get_settings.cache_clear()
    reviewer_id = _seed_subject(database_url, "REVIEWER")
    editor_id = _seed_subject(database_url, "EDITOR")

    try:
        app = create_app()
        proposals, candidate = _seed_candidate(app)
        reviewer, reviewer_csrf = _admin_client(app, reviewer_id)
        review_ids: dict[UUID, UUID] = {}
        for proposal in proposals:
            response = reviewer.post(
                f"/internal/admin/v1/proposals/{proposal.id}/review",
                headers={ADMIN_CSRF_HEADER: reviewer_csrf},
                json={
                    "decision": "ACCEPTED",
                    "policy_version": "proposal-review-v1",
                },
            )
            assert response.status_code == 201
            body = response.json()
            assert body["reviewer_ref"] == f"admin:{reviewer_id}"
            review_ids[proposal.id] = UUID(body["proposal_review_decision_id"])

        engine = create_engine(database_url)
        with engine.connect() as connection:
            before_projection = connection.execute(
                text(
                    """
                    SELECT count(*) FROM editorial.projection_record
                    WHERE candidate_proposal_id = :candidate_id
                    """
                ),
                {"candidate_id": candidate.id},
            ).scalar_one()
        assert before_projection == 0

        editor, editor_csrf = _admin_client(app, editor_id)
        path = f"/internal/admin/v1/candidate-proposals/{candidate.id}/projection"
        payload = {
            "proposal_review_decision_id": str(review_ids[candidate.id]),
            "profile_code": "CANDIDATE_TO_AUTHORING",
            "profile_version": 1,
            "idempotency_key": f"admin-operations-pg-{uuid4()}",
        }
        first = editor.post(
            path,
            headers={ADMIN_CSRF_HEADER: editor_csrf},
            json=payload,
        )
        replay = editor.post(
            path,
            headers={ADMIN_CSRF_HEADER: editor_csrf},
            json=payload,
        )

        assert first.status_code == 200
        assert replay.status_code == 200
        first_body = first.json()
        replay_body = replay.json()
        assert first_body["lifecycle_state"] == "DRAFT"
        assert first_body["replayed"] is False
        assert replay_body["replayed"] is True
        assert first_body["projection_record_id"] == replay_body["projection_record_id"]

        with engine.connect() as connection:
            review_rows = connection.execute(
                text(
                    """
                    SELECT reviewer_ref, decision
                    FROM ingestion.proposal_review_decision
                    WHERE proposal_id = :candidate_id
                    """
                ),
                {"candidate_id": candidate.id},
            ).mappings().all()
            row = connection.execute(
                text(
                    """
                    SELECT pr.requested_by_admin_ref, cv.lifecycle_state,
                           la.actor_ref, la.command
                    FROM editorial.projection_record pr
                    JOIN editorial.case_version cv
                      ON cv.id = pr.authoring_case_version_id
                    JOIN editorial.lifecycle_audit la
                      ON la.case_version_id = cv.id
                    WHERE pr.id = :record_id
                    """
                ),
                {"record_id": UUID(first_body["projection_record_id"])},
            ).mappings().one()
            consumer_count = connection.execute(
                text(
                    """
                    SELECT count(*) FROM content.case_version
                    WHERE id = :version_id
                    """
                ),
                {"version_id": UUID(first_body["authoring_case_version_id"])},
            ).scalar_one()

        assert review_rows == [
            {"reviewer_ref": f"admin:{reviewer_id}", "decision": "ACCEPTED"}
        ]
        assert row["requested_by_admin_ref"] == f"admin:{editor_id}"
        assert row["actor_ref"] == f"admin:{editor_id}"
        assert row["lifecycle_state"] == "DRAFT"
        assert row["command"] == "project_candidate_case"
        assert consumer_count == 0
    finally:
        get_settings.cache_clear()
