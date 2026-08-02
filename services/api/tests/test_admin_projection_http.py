from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from kefe_api.core.settings import get_settings
from kefe_api.main import create_app
from kefe_api.modules.admin_security.models import AdminRole
from kefe_api.modules.admin_security.router import ADMIN_CSRF_HEADER, ADMIN_SESSION_COOKIE
from kefe_api.modules.ingestion_orchestration.models import (
    ExecutorKind,
    InputArtifactKind,
    ProposalDraft,
    ProposalReviewDecisionKind,
    StageProcessorResult,
)


@dataclass
class StaticProcessor:
    drafts: tuple[ProposalDraft, ...]

    def process(self, **_kwargs) -> StageProcessorResult:
        return StageProcessorResult(proposals=self.drafts)


def _seed_reviewed_candidate(app) -> tuple[UUID, UUID]:
    service = app.state.ingestion_orchestration_service
    repository = app.state.ingestion_orchestration_repository
    run = service.start_run(
        input_artifact_kind=InputArtifactKind.SOURCE_ARTIFACT,
        input_artifact_id=uuid4(),
        input_content_hash=f"http-source-{uuid4()}",
        pipeline_code="candidate-extraction",
        pipeline_version="1.0.0",
        configuration_hash="config-v1",
        locale="en",
    )
    service.execute_stage(
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
    dependencies = repository.list_proposals(run.id)
    service.execute_stage(
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
                    payload={
                        "slug": f"admin-http-projection-{uuid4().hex[:8]}",
                        "title": "Admin HTTP projected Candidate Case",
                        "summary": "Secured HTTP projection test.",
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
    proposals = repository.list_proposals(run.id)
    reviews = {
        proposal.id: service.review_proposal(
            proposal_id=proposal.id,
            decision=ProposalReviewDecisionKind.ACCEPTED,
            reviewer_ref=f"reviewer:{proposal.id}",
        )
        for proposal in proposals
    }
    service.mark_succeeded(run.id)
    candidate = next(
        proposal for proposal in proposals if proposal.proposal_kind == "CANDIDATE_CASE"
    )
    return candidate.id, reviews[candidate.id].id


def _client(app, role: AdminRole) -> tuple[TestClient, str, UUID]:
    subject_id = uuid4()
    app.state.admin_session_store.upsert_subject(
        subject_id,
        roles=frozenset({role}),
    )
    now = datetime.now(UTC)
    issued = app.state.admin_session_store.issue(
        admin_subject_id=subject_id,
        authenticated_at=now,
        mfa_satisfied_at=now,
        expires_at=now + timedelta(hours=1),
    )
    client = TestClient(app)
    client.cookies.set(ADMIN_SESSION_COOKIE, issued.session_token)
    return client, issued.csrf_token, subject_id


def _payload(review_id: UUID, *, key: str = "projection-http-1") -> dict[str, object]:
    return {
        "proposal_review_decision_id": str(review_id),
        "profile_code": "CANDIDATE_TO_AUTHORING",
        "profile_version": 1,
        "idempotency_key": key,
    }


def _app(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("KEFE_PERSISTENCE_BACKEND", "memory")
    get_settings.cache_clear()
    return create_app()


def test_admin_projection_http_creates_draft_and_replays(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _app(monkeypatch)
    try:
        candidate_id, review_id = _seed_reviewed_candidate(app)
        client, csrf, subject_id = _client(app, AdminRole.EDITOR)
        path = f"/internal/admin/v1/candidate-proposals/{candidate_id}/projection"

        first = client.post(
            path,
            headers={ADMIN_CSRF_HEADER: csrf},
            json=_payload(review_id),
        )
        replay = client.post(
            path,
            headers={ADMIN_CSRF_HEADER: csrf},
            json=_payload(review_id),
        )

        assert first.status_code == 200
        assert replay.status_code == 200
        first_body = first.json()
        replay_body = replay.json()
        assert first_body["lifecycle_state"] == "DRAFT"
        assert first_body["replayed"] is False
        assert replay_body["replayed"] is True
        assert replay_body["projection_record_id"] == first_body["projection_record_id"]
        assert replay_body["authoring_case_version_id"] == (
            first_body["authoring_case_version_id"]
        )
        version = app.state.content_authoring_repository.get_version(
            UUID(first_body["authoring_case_version_id"])
        )
        assert version is not None
        assert version.state.value == "DRAFT"
        audit = app.state.content_authoring_repository.list_audit(version.case_id)
        assert audit[0].actor_ref == f"admin:{subject_id}"
    finally:
        get_settings.cache_clear()


def test_admin_projection_http_rejects_missing_csrf_and_wrong_role(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _app(monkeypatch)
    try:
        candidate_id, review_id = _seed_reviewed_candidate(app)
        editor, _csrf, _ = _client(app, AdminRole.EDITOR)
        reviewer, reviewer_csrf, _ = _client(app, AdminRole.REVIEWER)
        path = f"/internal/admin/v1/candidate-proposals/{candidate_id}/projection"

        missing_csrf = editor.post(path, json=_payload(review_id))
        forbidden = reviewer.post(
            path,
            headers={ADMIN_CSRF_HEADER: reviewer_csrf},
            json=_payload(review_id, key="reviewer-attempt"),
        )

        assert missing_csrf.status_code == 403
        assert missing_csrf.json()["code"] == "ADMIN_CSRF_REQUIRED"
        assert forbidden.status_code == 403
        assert forbidden.json()["code"] == "ADMIN_FORBIDDEN"
        assert app.state.editorial_projection_repository.get_by_candidate(
            candidate_id
        ) is None
    finally:
        get_settings.cache_clear()


def test_admin_projection_http_forbids_actor_and_incomplete_flow_pair(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _app(monkeypatch)
    try:
        candidate_id, review_id = _seed_reviewed_candidate(app)
        client, csrf, _ = _client(app, AdminRole.EDITOR)
        path = f"/internal/admin/v1/candidate-proposals/{candidate_id}/projection"

        actor_payload = _payload(review_id)
        actor_payload["actor_ref"] = "admin:spoofed"
        actor = client.post(
            path,
            headers={ADMIN_CSRF_HEADER: csrf},
            json=actor_payload,
        )
        incomplete_flow = client.post(
            path,
            headers={ADMIN_CSRF_HEADER: csrf},
            json={
                **_payload(review_id, key="incomplete-flow"),
                "explicit_flow_template_code": "STANDARD_COMMIT_REVEAL",
            },
        )

        assert actor.status_code == 422
        assert incomplete_flow.status_code == 422
        assert app.state.editorial_projection_repository.get_by_candidate(
            candidate_id
        ) is None
    finally:
        get_settings.cache_clear()
