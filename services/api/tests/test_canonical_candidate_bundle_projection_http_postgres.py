from __future__ import annotations

import os
from uuid import UUID

import pytest

from kefe_api.core.settings import get_settings
from kefe_api.main import create_app
from kefe_api.modules.admin_security.router import ADMIN_CSRF_HEADER
from kefe_api.modules.content_authoring.models import ContentLifecycle
from kefe_api.modules.ingestion_orchestration.models import (
    IngestionRunState,
    ProposalReviewDecisionKind,
)
from tests.test_admin_editorial_operations_http import _projection_payload, _review
from tests.test_admin_http_postgres import _admin_client, _seed_subject
from tests.test_admin_source_brief_review_http_postgres import _seed_feed_item
from tests.test_canonical_candidate_bundle_projection_http import _configuration

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)


def test_postgres_candidate_bundle_and_projection_survive_restarts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = os.environ["KEFE_DATABASE_URL"]
    monkeypatch.setenv("KEFE_PERSISTENCE_BACKEND", "postgres")
    monkeypatch.setenv("KEFE_API_VERSION", "0.25.0")
    get_settings.cache_clear()

    reviewer_id = _seed_subject(database_url, "REVIEWER")
    editor_id = _seed_subject(database_url, "EDITOR")
    try:
        first_app = create_app()
        reviewer, reviewer_csrf = _admin_client(first_app, reviewer_id)
        feed_item_id, _source = _seed_feed_item(first_app)

        accepted_parent = reviewer.post(
            f"/internal/admin/v1/proposals/{feed_item_id}/review",
            headers={ADMIN_CSRF_HEADER: reviewer_csrf},
            json={"decision": "ACCEPTED", "policy_version": "pg-parent-v1"},
        )
        assert accepted_parent.status_code == 201
        built_brief = reviewer.post(
            f"/internal/admin/v1/feed-items/{feed_item_id}/source-brief",
            headers={ADMIN_CSRF_HEADER: reviewer_csrf},
        )
        assert built_brief.status_code == 200
        source_brief_id = UUID(built_brief.json()["source_brief_proposal_id"])
        accepted_brief = _review(reviewer, reviewer_csrf, source_brief_id)
        assert accepted_brief.status_code == 201
        source_brief_review_id = UUID(
            accepted_brief.json()["proposal_review_decision_id"]
        )

        built_bundle = reviewer.post(
            f"/internal/admin/v1/source-briefs/{source_brief_id}/candidate-bundle",
            headers={ADMIN_CSRF_HEADER: reviewer_csrf},
            json=_configuration(source_brief_review_id),
        )
        assert built_bundle.status_code == 200
        body = built_bundle.json()
        seed_id = UUID(body["candidate_seed_artifact_id"])
        run_id = UUID(body["run_id"])
        dependency_ids = (
            UUID(body["decision_problem_proposal_id"]),
            UUID(body["question_draft_proposal_id"]),
        )
        candidate_id = UUID(body["candidate_case_proposal_id"])

        second_app = create_app()
        repository = second_app.state.ingestion_orchestration_repository
        run = repository.get_run(run_id)
        assert run is not None
        assert run.state is IngestionRunState.SUCCEEDED
        assert second_app.state.knowledge_repository.get_normalized_artifact(seed_id) is not None
        proposals = tuple(
            repository.get_proposal(proposal_id)
            for proposal_id in (*dependency_ids, candidate_id)
        )
        assert all(proposal is not None for proposal in proposals)
        assert tuple(proposal.proposal_kind for proposal in proposals if proposal) == (
            "DECISION_PROBLEM",
            "QUESTION_DRAFT",
            "CANDIDATE_CASE",
        )
        assert all(
            repository.get_review_decision(proposal_id) is None
            for proposal_id in (*dependency_ids, candidate_id)
        )

        second_reviewer, second_reviewer_csrf = _admin_client(
            second_app,
            reviewer_id,
        )
        candidate_review = _review(
            second_reviewer,
            second_reviewer_csrf,
            candidate_id,
        )
        assert candidate_review.status_code == 201
        candidate_review_id = UUID(
            candidate_review.json()["proposal_review_decision_id"]
        )
        assert (
            repository.get_review_decision(candidate_id).decision
            is ProposalReviewDecisionKind.ACCEPTED
        )

        editor, editor_csrf = _admin_client(second_app, editor_id)
        projection_path = (
            f"/internal/admin/v1/candidate-proposals/{candidate_id}/projection"
        )
        projection_payload = _projection_payload(
            candidate_review_id,
            f"pg-candidate-bundle-{candidate_id}",
        )
        blocked = editor.post(
            projection_path,
            headers={ADMIN_CSRF_HEADER: editor_csrf},
            json=projection_payload,
        )
        assert blocked.status_code == 422
        assert "EDITORIAL_PROJECTION_DEPENDENCY_NOT_READY" in blocked.text

        for dependency_id in dependency_ids:
            accepted = _review(
                second_reviewer,
                second_reviewer_csrf,
                dependency_id,
            )
            assert accepted.status_code == 201

        projected = editor.post(
            projection_path,
            headers={ADMIN_CSRF_HEADER: editor_csrf},
            json=projection_payload,
        )
        replay = editor.post(
            projection_path,
            headers={ADMIN_CSRF_HEADER: editor_csrf},
            json=projection_payload,
        )
        assert projected.status_code == 200
        assert replay.status_code == 200
        assert projected.json()["lifecycle_state"] == "DRAFT"
        assert projected.json()["replayed"] is False
        assert replay.json()["replayed"] is True
        projection_id = UUID(projected.json()["projection_record_id"])
        case_version_id = UUID(projected.json()["authoring_case_version_id"])

        third_app = create_app()
        persisted_projection = (
            third_app.state.editorial_projection_repository.get_by_candidate(
                candidate_id
            )
        )
        assert persisted_projection is not None
        assert persisted_projection.id == projection_id
        assert persisted_projection.authoring_case_version_id == case_version_id
        version = third_app.state.content_authoring_repository.get_version(
            case_version_id
        )
        assert version is not None
        assert version.state is ContentLifecycle.DRAFT
        assert third_app.state.ingestion_orchestration_repository.get_run(run_id) == run
    finally:
        get_settings.cache_clear()
