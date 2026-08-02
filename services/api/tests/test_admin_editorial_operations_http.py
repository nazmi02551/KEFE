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
    Proposal,
    ProposalDraft,
    StageProcessorResult,
)


@dataclass
class StaticProcessor:
    drafts: tuple[ProposalDraft, ...]

    def process(self, **_kwargs) -> StageProcessorResult:
        return StageProcessorResult(proposals=self.drafts)


def _app(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("KEFE_PERSISTENCE_BACKEND", "memory")
    get_settings.cache_clear()
    return create_app()


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


def _seed_candidate(app) -> tuple[tuple[Proposal, ...], Proposal]:
    service = app.state.ingestion_orchestration_service
    repository = app.state.ingestion_orchestration_repository
    run = service.start_run(
        input_artifact_kind=InputArtifactKind.SOURCE_ARTIFACT,
        input_artifact_id=uuid4(),
        input_content_hash=f"admin-operations-{uuid4()}",
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
                        "slug": f"admin-operations-{uuid4().hex[:8]}",
                        "title": "Admin operations Candidate Case",
                        "summary": "Separate review and projection commands.",
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


def _review(
    client: TestClient,
    csrf: str,
    proposal_id: UUID,
    *,
    decision: str = "ACCEPTED",
):
    return client.post(
        f"/internal/admin/v1/proposals/{proposal_id}/review",
        headers={ADMIN_CSRF_HEADER: csrf},
        json={
            "decision": decision,
            "rationale": "Reviewed against the bounded editorial policy.",
            "policy_version": "proposal-review-v1",
        },
    )


def _projection_payload(review_id: UUID, key: str) -> dict[str, object]:
    return {
        "proposal_review_decision_id": str(review_id),
        "profile_code": "CANDIDATE_TO_AUTHORING",
        "profile_version": 1,
        "idempotency_key": key,
    }


def test_proposal_review_is_terminal_server_derived_and_does_not_auto_project(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _app(monkeypatch)
    try:
        _proposals, candidate = _seed_candidate(app)
        reviewer, csrf, subject_id = _client(app, AdminRole.REVIEWER)

        response = _review(reviewer, csrf, candidate.id)
        duplicate = _review(reviewer, csrf, candidate.id)

        assert response.status_code == 201
        body = response.json()
        assert body["proposal_id"] == str(candidate.id)
        assert body["decision"] == "ACCEPTED"
        assert body["reviewer_ref"] == f"admin:{subject_id}"
        assert duplicate.status_code == 409
        assert duplicate.json()["code"] == "INGESTION_PROPOSAL_ALREADY_REVIEWED"
        assert app.state.editorial_projection_repository.get_by_candidate(
            candidate.id
        ) is None
    finally:
        get_settings.cache_clear()


def test_proposal_review_requires_csrf_capability_and_strict_identity_input(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _app(monkeypatch)
    try:
        proposals, candidate = _seed_candidate(app)
        reviewer, _csrf, _ = _client(app, AdminRole.REVIEWER)
        editor, editor_csrf, _ = _client(app, AdminRole.EDITOR)
        path = f"/internal/admin/v1/proposals/{candidate.id}/review"

        missing_csrf = reviewer.post(path, json={"decision": "ACCEPTED"})
        forbidden = editor.post(
            path,
            headers={ADMIN_CSRF_HEADER: editor_csrf},
            json={"decision": "ACCEPTED"},
        )
        spoofed = reviewer.post(
            f"/internal/admin/v1/proposals/{proposals[0].id}/review",
            headers={ADMIN_CSRF_HEADER: _csrf},
            json={
                "decision": "ACCEPTED",
                "reviewer_ref": "admin:spoofed",
            },
        )

        assert missing_csrf.status_code == 403
        assert missing_csrf.json()["code"] == "ADMIN_CSRF_REQUIRED"
        assert forbidden.status_code == 403
        assert forbidden.json()["code"] == "ADMIN_FORBIDDEN"
        assert spoofed.status_code == 422
    finally:
        get_settings.cache_clear()


def test_projection_is_a_separate_editor_command_and_replays_to_one_draft(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _app(monkeypatch)
    try:
        proposals, candidate = _seed_candidate(app)
        reviewer, reviewer_csrf, _ = _client(app, AdminRole.REVIEWER)
        review_ids: dict[UUID, UUID] = {}
        for proposal in proposals:
            response = _review(reviewer, reviewer_csrf, proposal.id)
            assert response.status_code == 201
            review_ids[proposal.id] = UUID(
                response.json()["proposal_review_decision_id"]
            )

        editor, editor_csrf, editor_id = _client(app, AdminRole.EDITOR)
        reviewer_projection, _, _ = _client(app, AdminRole.REVIEWER)
        path = f"/internal/admin/v1/candidate-proposals/{candidate.id}/projection"
        payload = _projection_payload(
            review_ids[candidate.id],
            key="admin-operations-projection-1",
        )

        forbidden = reviewer_projection.post(
            path,
            headers={ADMIN_CSRF_HEADER: reviewer_csrf},
            json=payload,
        )
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

        assert forbidden.status_code == 403
        assert forbidden.json()["code"] == "ADMIN_FORBIDDEN"
        assert first.status_code == 200
        assert replay.status_code == 200
        first_body = first.json()
        replay_body = replay.json()
        assert first_body["lifecycle_state"] == "DRAFT"
        assert first_body["replayed"] is False
        assert replay_body["replayed"] is True
        assert replay_body["projection_record_id"] == first_body["projection_record_id"]
        version = app.state.content_authoring_repository.get_version(
            UUID(first_body["authoring_case_version_id"])
        )
        assert version is not None
        assert version.state.value == "DRAFT"
        audit = app.state.content_authoring_repository.list_audit(version.case_id)
        assert audit[0].actor_ref == f"admin:{editor_id}"
        assert len(audit) == 1
        assert audit[0].command == "project_candidate_case"
    finally:
        get_settings.cache_clear()


def test_projection_forbids_actor_and_incomplete_flow_pair(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _app(monkeypatch)
    try:
        proposals, candidate = _seed_candidate(app)
        reviewer, reviewer_csrf, _ = _client(app, AdminRole.REVIEWER)
        reviews = {
            proposal.id: _review(reviewer, reviewer_csrf, proposal.id).json()
            for proposal in proposals
        }
        review_id = UUID(reviews[candidate.id]["proposal_review_decision_id"])
        editor, csrf, _ = _client(app, AdminRole.EDITOR)
        path = f"/internal/admin/v1/candidate-proposals/{candidate.id}/projection"

        actor_payload = _projection_payload(review_id, "actor-spoof")
        actor_payload["actor_ref"] = "admin:spoofed"
        actor = editor.post(
            path,
            headers={ADMIN_CSRF_HEADER: csrf},
            json=actor_payload,
        )
        incomplete_flow = editor.post(
            path,
            headers={ADMIN_CSRF_HEADER: csrf},
            json={
                **_projection_payload(review_id, "incomplete-flow"),
                "explicit_flow_template_code": "STANDARD_COMMIT_REVEAL",
            },
        )

        assert actor.status_code == 422
        assert incomplete_flow.status_code == 422
        assert app.state.editorial_projection_repository.get_by_candidate(
            candidate.id
        ) is None
    finally:
        get_settings.cache_clear()
