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
        proposal
        for proposal in proposals
        if proposal.proposal_kind == "CANDIDATE_CASE"
    )
    return proposals, candidate


def _review(
    client: TestClient,
    csrf: str,
    proposal_id: UUID,
    *,
    extra: dict[str, object] | None = None,
):
    body: dict[str, object] = {
        "decision": "ACCEPTED",
        "rationale": "Reviewed against the bounded editorial policy.",
        "policy_version": "proposal-review-v1",
    }
    body.update(extra or {})
    return client.post(
        f"/internal/admin/v1/proposals/{proposal_id}/review",
        headers={ADMIN_CSRF_HEADER: csrf},
        json=body,
    )


def _projection_payload(review_id: UUID, key: str) -> dict[str, object]:
    return {
        "proposal_review_decision_id": str(review_id),
        "profile_code": "CANDIDATE_TO_AUTHORING",
        "profile_version": 1,
        "idempotency_key": key,
    }


def test_review_is_terminal_server_derived_and_does_not_auto_project(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _app(monkeypatch)
    try:
        proposals, candidate = _seed_candidate(app)
        reviewer, reviewer_csrf, reviewer_id = _client(app, AdminRole.REVIEWER)
        editor, editor_csrf, _ = _client(app, AdminRole.EDITOR)

        response = _review(reviewer, reviewer_csrf, candidate.id)
        duplicate = _review(reviewer, reviewer_csrf, candidate.id)
        editor_attempt = _review(editor, editor_csrf, proposals[0].id)

        assert response.status_code == 201
        body = response.json()
        assert body["proposal_id"] == str(candidate.id)
        assert body["decision"] == "ACCEPTED"
        assert body["reviewer_ref"] == f"admin:{reviewer_id}"
        assert duplicate.status_code == 409
        assert duplicate.json()["code"] == "INGESTION_PROPOSAL_ALREADY_REVIEWED"
        assert editor_attempt.status_code == 403
        assert editor_attempt.json()["code"] == "ADMIN_FORBIDDEN"
        assert app.state.editorial_projection_repository.get_by_candidate(
            candidate.id
        ) is None
    finally:
        get_settings.cache_clear()


def test_review_requires_csrf_and_forbids_request_supplied_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _app(monkeypatch)
    try:
        proposals, candidate = _seed_candidate(app)
        reviewer, reviewer_csrf, _ = _client(app, AdminRole.REVIEWER)
        path = f"/internal/admin/v1/proposals/{candidate.id}/review"

        missing_csrf = reviewer.post(path, json={"decision": "ACCEPTED"})
        spoofed = _review(
            reviewer,
            reviewer_csrf,
            proposals[0].id,
            extra={"reviewer_ref": "admin:spoofed"},
        )

        assert missing_csrf.status_code == 403
        assert missing_csrf.json()["code"] == "ADMIN_CSRF_REQUIRED"
        assert spoofed.status_code == 422
    finally:
        get_settings.cache_clear()


def test_projection_is_explicit_editor_only_draft_and_idempotent(
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
        other_reviewer, other_reviewer_csrf, _ = _client(app, AdminRole.REVIEWER)
        path = (
            "/internal/admin/v1/candidate-proposals/"
            f"{candidate.id}/projection"
        )
        payload = _projection_payload(
            review_ids[candidate.id],
            "admin-operations-projection-1",
        )

        forbidden = other_reviewer.post(
            path,
            headers={ADMIN_CSRF_HEADER: other_reviewer_csrf},
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
        assert len(audit) == 1
        assert audit[0].actor_ref == f"admin:{editor_id}"
        assert audit[0].command == "project_candidate_case"
    finally:
        get_settings.cache_clear()
