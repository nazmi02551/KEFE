from __future__ import annotations

from uuid import UUID

import pytest

from kefe_api.core.settings import get_settings
from kefe_api.modules.admin_security.models import AdminRole
from kefe_api.modules.admin_security.router import ADMIN_CSRF_HEADER
from kefe_api.modules.ingestion_orchestration.models import ProposalReviewDecisionKind
from tests.test_admin_editorial_operations_http import (
    _client as _editorial_client,
)
from tests.test_admin_editorial_operations_http import (
    _projection_payload,
    _review,
)
from tests.test_admin_source_brief_review_http import (
    _accept_and_build,
    _admin,
    _app,
    _seed_feed_item,
)


def _configuration(review_id: UUID) -> dict[str, object]:
    return {
        "source_brief_review_decision_id": str(review_id),
        "slug": "canonical-candidate-bundle",
        "title": "Canonical Candidate Bundle",
        "summary": "Explicit editorial configuration from an accepted Source Brief.",
        "base_format_code": "DILEMMA",
        "primary_domain_code": "DAILY_LIFE",
        "content_risk": "L0",
        "issue_code": "PRIMARY",
        "issue_title": "Primary decision",
        "question_stable_code": "PRIMARY_DECISION",
        "question_prompt": "Which option should be selected?",
        "response_options": ["OPTION_A", "OPTION_B"],
        "flow_template_code": "STANDARD_COMMIT_REVEAL",
        "flow_template_version_no": 1,
        "content_locale": "tr-TR",
        "market_scope": "GLOBAL",
        "country_codes": [],
        "required_review_modes": ["EDITORIAL"],
        "is_fact_bearing": True,
        "is_real_event": True,
        "context_title": "What is known",
        "cultural_context_note": None,
        "legal_context_note": None,
    }


def _accepted_source_brief(app, reviewer, csrf: str) -> tuple[UUID, UUID]:
    feed_item_id, _source = _seed_feed_item(app, index=1)
    source_brief_id = _accept_and_build(reviewer, csrf, feed_item_id)
    accepted = _review(reviewer, csrf, source_brief_id)
    assert accepted.status_code == 201
    return source_brief_id, UUID(accepted.json()["proposal_review_decision_id"])


def test_candidate_bundle_is_025_only_secured_explicit_and_idempotent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    old_app = _app(monkeypatch, version="0.24.0")
    old_reviewer, old_csrf = _admin(old_app, AdminRole.REVIEWER)
    old_response = old_reviewer.post(
        "/internal/admin/v1/source-briefs/00000000-0000-0000-0000-000000000001/candidate-bundle",
        headers={ADMIN_CSRF_HEADER: old_csrf},
        json=_configuration(UUID(int=1)),
    )
    assert old_response.status_code == 404

    app = _app(monkeypatch, version="0.25.0")
    try:
        reviewer, csrf = _admin(app, AdminRole.REVIEWER)
        editor, editor_csrf = _admin(app, AdminRole.EDITOR)
        source_brief_id, review_id = _accepted_source_brief(app, reviewer, csrf)
        path = f"/internal/admin/v1/source-briefs/{source_brief_id}/candidate-bundle"
        payload = _configuration(review_id)

        missing_csrf = reviewer.post(path, json=payload)
        forbidden = editor.post(
            path,
            headers={ADMIN_CSRF_HEADER: editor_csrf},
            json=payload,
        )
        first = reviewer.post(
            path,
            headers={ADMIN_CSRF_HEADER: csrf},
            json=payload,
        )
        replay = reviewer.post(
            path,
            headers={ADMIN_CSRF_HEADER: csrf},
            json=payload,
        )

        assert missing_csrf.status_code == 403
        assert forbidden.status_code == 403
        assert first.status_code == 200
        assert replay.status_code == 200
        assert replay.json() == first.json()
        body = first.json()
        assert body["run_state"] == "SUCCEEDED"
        assert body["proposal_review_state"] == "PENDING"
        ids = (
            UUID(body["decision_problem_proposal_id"]),
            UUID(body["question_draft_proposal_id"]),
            UUID(body["candidate_case_proposal_id"]),
        )
        repository = app.state.ingestion_orchestration_repository
        proposals = tuple(repository.get_proposal(proposal_id) for proposal_id in ids)
        assert all(proposal is not None for proposal in proposals)
        assert tuple(proposal.proposal_kind for proposal in proposals if proposal) == (
            "DECISION_PROBLEM",
            "QUESTION_DRAFT",
            "CANDIDATE_CASE",
        )
        assert all(
            repository.get_review_decision(proposal_id) is None
            for proposal_id in ids
        )
        assert all(
            repository.find_materialization(proposal_id) is None
            for proposal_id in ids
        )
        candidate = proposals[2]
        assert candidate is not None
        assert candidate.payload["dependency_ids"] == [str(ids[0]), str(ids[1])]
        assert "raw_body" not in candidate.payload
        assert "backend_object_key" not in candidate.payload
    finally:
        get_settings.cache_clear()


def test_candidate_bundle_projection_requires_separate_reviews_and_creates_one_draft(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _app(monkeypatch, version="0.25.0")
    try:
        reviewer, reviewer_csrf = _admin(app, AdminRole.REVIEWER)
        source_brief_id, source_brief_review_id = _accepted_source_brief(
            app,
            reviewer,
            reviewer_csrf,
        )
        built = reviewer.post(
            f"/internal/admin/v1/source-briefs/{source_brief_id}/candidate-bundle",
            headers={ADMIN_CSRF_HEADER: reviewer_csrf},
            json=_configuration(source_brief_review_id),
        )
        assert built.status_code == 200
        body = built.json()
        dependency_ids = (
            UUID(body["decision_problem_proposal_id"]),
            UUID(body["question_draft_proposal_id"]),
        )
        candidate_id = UUID(body["candidate_case_proposal_id"])

        candidate_review = _review(reviewer, reviewer_csrf, candidate_id)
        assert candidate_review.status_code == 201
        candidate_review_id = UUID(
            candidate_review.json()["proposal_review_decision_id"]
        )
        assert (
            app.state.ingestion_orchestration_repository.get_review_decision(
                candidate_id
            ).decision
            is ProposalReviewDecisionKind.ACCEPTED
        )

        editor, editor_csrf, _editor_id = _editorial_client(app, AdminRole.EDITOR)
        projection_path = (
            f"/internal/admin/v1/candidate-proposals/{candidate_id}/projection"
        )
        projection_payload = _projection_payload(
            candidate_review_id,
            "canonical-candidate-bundle-projection-1",
        )
        blocked = editor.post(
            projection_path,
            headers={ADMIN_CSRF_HEADER: editor_csrf},
            json=projection_payload,
        )
        assert blocked.status_code == 409
        assert app.state.editorial_projection_repository.get_by_candidate(
            candidate_id
        ) is None

        for dependency_id in dependency_ids:
            accepted = _review(reviewer, reviewer_csrf, dependency_id)
            assert accepted.status_code == 201

        first = editor.post(
            projection_path,
            headers={ADMIN_CSRF_HEADER: editor_csrf},
            json=projection_payload,
        )
        replay = editor.post(
            projection_path,
            headers={ADMIN_CSRF_HEADER: editor_csrf},
            json=projection_payload,
        )
        assert first.status_code == 200
        assert replay.status_code == 200
        assert first.json()["lifecycle_state"] == "DRAFT"
        assert first.json()["replayed"] is False
        assert replay.json()["replayed"] is True
        assert replay.json()["projection_record_id"] == first.json()[
            "projection_record_id"
        ]
        version = app.state.content_authoring_repository.get_version(
            UUID(first.json()["authoring_case_version_id"])
        )
        assert version is not None
        assert version.state.value == "DRAFT"
        assert len(
            app.state.content_authoring_repository.list_audit(version.case_id)
        ) == 1
    finally:
        get_settings.cache_clear()
