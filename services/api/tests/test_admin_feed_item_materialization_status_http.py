from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

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
    ProposalMaterialization,
    ProposalReviewDecisionKind,
    StageProcessorResult,
)
from kefe_api.modules.knowledge.models import SourceArtifact
from kefe_api.modules.knowledge.source_evidence import (
    canonical_content_hash,
    canonical_storage_ref,
)


class FixedProposalProcessor:
    def __init__(self, proposal: ProposalDraft) -> None:
        self._proposal = proposal

    def process(self, **_) -> StageProcessorResult:
        return StageProcessorResult(proposals=(self._proposal,))


def _app(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("KEFE_PERSISTENCE_BACKEND", "memory")
    get_settings.cache_clear()
    return create_app()


def _admin(app, role: AdminRole) -> tuple[TestClient, str]:
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
    return client, issued.csrf_token


def _seed(app, *, kind: str = "FEED_ITEM"):
    knowledge = app.state.knowledge_repository
    service = app.state.ingestion_orchestration_service
    repository = app.state.ingestion_orchestration_repository
    content_hash = canonical_content_hash(f"status-feed-{uuid4()}".encode())
    source = knowledge.add_source_artifact(
        SourceArtifact.create(
            adapter_code="test.status.rss.v1",
            external_locator=f"https://feeds.example.test/{uuid4()}.xml",
            captured_at=datetime(2026, 8, 3, 6, 0, tzinfo=UTC),
            content_hash=content_hash,
            language_code="en",
            jurisdiction_code="GB",
            raw_storage_ref=canonical_storage_ref(content_hash),
        )
    )
    if kind == "FEED_ITEM":
        draft = ProposalDraft(
            proposal_kind="FEED_ITEM",
            payload_schema_ref="kefe.feed-item",
            payload_schema_version="1.0.0",
            payload={
                "source_artifact_id": str(source.id),
                "feed_content_hash": source.content_hash,
                "feed_storage_ref": source.raw_storage_ref,
                "feed_format": "RSS_2_0",
                "feed_title": "Status Feed",
                "item_id": f"urn:status:{uuid4()}",
                "item_title": "Status item",
                "item_url": "https://news.example.test/status-item",
                "published_at": "2026-08-03T05:55:00+00:00",
                "summary_text": "Status summary.",
            },
            risk_code="UNREVIEWED_EXTERNAL_FEED_ITEM",
            provenance_ref=source.raw_storage_ref,
        )
    else:
        draft = ProposalDraft(
            proposal_kind="CLAIM",
            payload_schema_ref="knowledge/claim",
            payload_schema_version="1",
            payload={"normalized_text": "Unsupported", "language_code": "en"},
        )
    run = service.start_run(
        input_artifact_kind=InputArtifactKind.SOURCE_ARTIFACT,
        input_artifact_id=source.id,
        input_content_hash=source.content_hash,
        pipeline_code=f"STATUS_{uuid4()}",
        pipeline_version="1.0.0",
        configuration_hash=f"sha256:status-{uuid4()}",
    )
    service.execute_stage(
        run_id=run.id,
        stage_code="PROPOSE",
        stage_version="1.0.0",
        input_hash=source.content_hash,
        max_attempts=1,
        executor_kind=ExecutorKind.DETERMINISTIC,
        processor=FixedProposalProcessor(draft),
    )
    return repository.list_proposals(run.id)[0]


def _path(proposal_id) -> str:
    return (
        f"/internal/admin/v1/proposals/{proposal_id}/"
        "feed-item-materialization-status"
    )


def test_status_requires_auth_and_both_capabilities_without_csrf(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _app(monkeypatch)
    try:
        proposal = _seed(app)
        anonymous = TestClient(app).get(_path(proposal.id))
        editor, _ = _admin(app, AdminRole.EDITOR)
        publisher, _ = _admin(app, AdminRole.PUBLISHER)
        reviewer, _ = _admin(app, AdminRole.REVIEWER)

        assert anonymous.status_code == 401
        assert anonymous.json()["code"] == "ADMIN_AUTH_REQUIRED"
        assert editor.get(_path(proposal.id)).status_code == 403
        assert publisher.get(_path(proposal.id)).status_code == 403
        response = reviewer.get(_path(proposal.id))
        assert response.status_code == 200
        assert response.json()["status"] == "REVIEW_REQUIRED"
    finally:
        get_settings.cache_clear()


def test_status_progresses_review_required_ready_materialized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _app(monkeypatch)
    try:
        proposal = _seed(app)
        service = app.state.ingestion_orchestration_service
        reviewer, csrf = _admin(app, AdminRole.REVIEWER)

        initial = reviewer.get(_path(proposal.id))
        assert initial.status_code == 200
        assert initial.json()["status"] == "REVIEW_REQUIRED"
        assert initial.json()["proposal_review_decision_id"] is None
        assert initial.json()["target_id"] is None

        review = service.review_proposal(
            proposal_id=proposal.id,
            decision=ProposalReviewDecisionKind.ACCEPTED,
            reviewer_ref="admin:status-reviewer",
        )
        ready = reviewer.get(_path(proposal.id))
        assert ready.status_code == 200
        assert ready.json()["status"] == "READY"
        assert ready.json()["proposal_review_decision_id"] == str(review.id)
        assert ready.json()["proposal_review_decision"] == "ACCEPTED"
        assert ready.json()["target_id"] is None

        command = reviewer.post(
            f"/internal/admin/v1/proposals/{proposal.id}/feed-item-materialization",
            headers={ADMIN_CSRF_HEADER: csrf},
            json={"proposal_review_decision_id": str(review.id)},
        )
        assert command.status_code == 200

        materialized = reviewer.get(_path(proposal.id))
        assert materialized.status_code == 200
        body = materialized.json()
        assert body["status"] == "MATERIALIZED"
        assert body["proposal_review_decision_id"] == str(review.id)
        assert body["proposal_materialization_id"] is not None
        assert body["target_kind"] == "NORMALIZED_ARTIFACT"
        assert body["target_id"] is not None
        assert body["materialized_at"] is not None
        forbidden = {"payload", "text", "metadata", "evidence", "rationale"}
        assert forbidden.isdisjoint(body)
    finally:
        get_settings.cache_clear()


def test_rejected_unsupported_and_conflicting_statuses_are_bounded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _app(monkeypatch)
    try:
        reviewer, _ = _admin(app, AdminRole.REVIEWER)
        service = app.state.ingestion_orchestration_service
        repository = app.state.ingestion_orchestration_repository

        rejected_proposal = _seed(app)
        rejected_review = service.review_proposal(
            proposal_id=rejected_proposal.id,
            decision=ProposalReviewDecisionKind.REJECTED,
            reviewer_ref="admin:status-reviewer",
        )
        rejected = reviewer.get(_path(rejected_proposal.id))
        assert rejected.status_code == 200
        assert rejected.json()["status"] == "REVIEW_REQUIRED"
        assert rejected.json()["proposal_review_decision_id"] == str(
            rejected_review.id
        )
        assert rejected.json()["proposal_review_decision"] == "REJECTED"

        unsupported = _seed(app, kind="CLAIM")
        unsupported_response = reviewer.get(_path(unsupported.id))
        assert unsupported_response.status_code == 422
        assert unsupported_response.json()["code"] == (
            "INGESTION_FEED_ITEM_MATERIALIZATION_UNSUPPORTED"
        )

        conflict_proposal = _seed(app)
        accepted = service.review_proposal(
            proposal_id=conflict_proposal.id,
            decision=ProposalReviewDecisionKind.ACCEPTED,
            reviewer_ref="admin:status-reviewer",
        )
        repository.add_materialization(
            ProposalMaterialization(
                id=uuid4(),
                proposal_id=conflict_proposal.id,
                review_decision_id=accepted.id,
                target_kind="CLAIM",
                target_id=uuid4(),
                materialized_at=datetime.now(UTC),
            )
        )
        conflict = reviewer.get(_path(conflict_proposal.id))
        assert conflict.status_code == 409
        assert conflict.json()["code"] == (
            "INGESTION_FEED_ITEM_MATERIALIZATION_STATUS_CONFLICT"
        )
    finally:
        get_settings.cache_clear()
