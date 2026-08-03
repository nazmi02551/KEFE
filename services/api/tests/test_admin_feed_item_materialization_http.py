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
from kefe_api.modules.knowledge.models import SourceArtifact
from kefe_api.modules.knowledge.source_evidence import (
    canonical_content_hash,
    canonical_storage_ref,
)


@dataclass
class StaticProcessor:
    draft: ProposalDraft

    def process(self, **_kwargs) -> StageProcessorResult:
        return StageProcessorResult(proposals=(self.draft,))


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


def _seed_proposal(
    app,
    *,
    proposal_kind: str = "FEED_ITEM",
    schema_ref: str = "kefe.feed-item",
    schema_version: str = "1.0.0",
) -> Proposal:
    source_body = f"feed-item-http:{uuid4()}".encode()
    source_hash = canonical_content_hash(source_body)
    source = app.state.knowledge_repository.add_source_artifact(
        SourceArtifact.create(
            adapter_code="test.admin_feed_item.v1",
            external_locator=f"https://feeds.example.test/{uuid4()}.xml",
            captured_at=datetime.now(UTC),
            content_hash=source_hash,
            publisher_or_issuer="Admin HTTP Feed",
            language_code="en",
            jurisdiction_code="ZZ",
            raw_storage_ref=canonical_storage_ref(source_hash),
        )
    )
    service = app.state.ingestion_orchestration_service
    repository = app.state.ingestion_orchestration_repository
    run = service.start_run(
        input_artifact_kind=InputArtifactKind.SOURCE_ARTIFACT,
        input_artifact_id=source.id,
        input_content_hash=source.content_hash,
        pipeline_code="RSS_ATOM_FEED_ITEM_EXTRACTION",
        pipeline_version="1.0.0",
        configuration_hash=f"sha256:{uuid4().hex}{uuid4().hex}",
        locale="en",
        jurisdiction_code="ZZ",
    )
    payload: dict[str, object]
    if proposal_kind == "FEED_ITEM":
        payload = {
            "source_artifact_id": str(source.id),
            "feed_content_hash": source.content_hash,
            "feed_storage_ref": source.raw_storage_ref,
            "feed_format": "RSS_2_0",
            "feed_title": "Admin HTTP Feed",
            "item_id": f"feed-item-{uuid4()}",
            "item_title": "Admin reviewed feed item",
            "item_url": "https://www.example.test/admin-feed-item",
            "published_at": "2026-08-03T09:55:00+00:00",
            "summary_text": "Materialization remains a separate explicit command.",
        }
    else:
        payload = {"title": "Not a feed item"}
    service.execute_stage(
        run_id=run.id,
        stage_code="EXTRACT_FEED_ITEMS",
        stage_version="1.0.0",
        input_hash=source.content_hash,
        max_attempts=1,
        executor_kind=ExecutorKind.DETERMINISTIC,
        processor=StaticProcessor(
            ProposalDraft(
                proposal_kind=proposal_kind,
                payload_schema_ref=schema_ref,
                payload_schema_version=schema_version,
                payload=payload,
                provenance_ref=source.raw_storage_ref,
            )
        ),
    )
    return repository.list_proposals(run.id)[0]


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
            "rationale": "Explicit human review before materialization.",
            "policy_version": "feed-item-review-v1",
        },
    )


def _materialize(
    client: TestClient,
    csrf: str,
    proposal_id: UUID,
    review_id: UUID,
    *,
    extra: dict[str, object] | None = None,
):
    body: dict[str, object] = {
        "proposal_review_decision_id": str(review_id),
    }
    body.update(extra or {})
    return client.post(
        "/internal/admin/v1/feed-item-proposals/"
        f"{proposal_id}/materialization",
        headers={ADMIN_CSRF_HEADER: csrf},
        json=body,
    )


def test_accepted_feed_item_materialization_is_explicit_and_idempotent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _app(monkeypatch)
    try:
        proposal = _seed_proposal(app)
        reviewer, csrf, _ = _client(app, AdminRole.REVIEWER)
        review_response = _review(reviewer, csrf, proposal.id)
        assert review_response.status_code == 201
        review_id = UUID(review_response.json()["proposal_review_decision_id"])

        first = _materialize(reviewer, csrf, proposal.id, review_id)
        replay = _materialize(reviewer, csrf, proposal.id, review_id)

        assert first.status_code == 200
        assert replay.status_code == 200
        first_body = first.json()
        replay_body = replay.json()
        assert first_body["proposal_id"] == str(proposal.id)
        assert first_body["proposal_review_decision_id"] == str(review_id)
        assert first_body["target_kind"] == "NORMALIZED_ARTIFACT"
        assert first_body["replayed"] is False
        assert replay_body["replayed"] is True
        assert replay_body["proposal_materialization_id"] == (
            first_body["proposal_materialization_id"]
        )
        assert replay_body["target_id"] == first_body["target_id"]
        artifact = app.state.knowledge_repository.get_normalized_artifact(
            UUID(first_body["target_id"])
        )
        assert artifact is not None
        assert artifact.media_metadata["proposal_id"] == str(proposal.id)
        assert "feed_storage_ref" not in artifact.media_metadata
    finally:
        get_settings.cache_clear()


def test_materialization_requires_session_csrf_and_source_verify_capability(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _app(monkeypatch)
    try:
        proposal = _seed_proposal(app)
        reviewer, reviewer_csrf, _ = _client(app, AdminRole.REVIEWER)
        review = _review(reviewer, reviewer_csrf, proposal.id)
        review_id = UUID(review.json()["proposal_review_decision_id"])
        path = (
            "/internal/admin/v1/feed-item-proposals/"
            f"{proposal.id}/materialization"
        )

        missing_csrf = reviewer.post(
            path,
            json={"proposal_review_decision_id": str(review_id)},
        )
        editor, editor_csrf, _ = _client(app, AdminRole.EDITOR)
        forbidden = _materialize(
            editor,
            editor_csrf,
            proposal.id,
            review_id,
        )
        extra = _materialize(
            reviewer,
            reviewer_csrf,
            proposal.id,
            review_id,
            extra={"target_kind": "CLAIM"},
        )

        assert missing_csrf.status_code == 403
        assert missing_csrf.json()["code"] == "ADMIN_CSRF_REQUIRED"
        assert forbidden.status_code == 403
        assert forbidden.json()["code"] == "ADMIN_FORBIDDEN"
        assert extra.status_code == 422
        assert app.state.ingestion_orchestration_repository.find_materialization(
            proposal.id,
            target_kind="NORMALIZED_ARTIFACT",
        ) is None
    finally:
        get_settings.cache_clear()


@pytest.mark.parametrize("decision", ["REJECTED", "CHANGES_REQUESTED"])
def test_negative_review_and_wrong_review_id_fail_before_writes(
    monkeypatch: pytest.MonkeyPatch,
    decision: str,
) -> None:
    app = _app(monkeypatch)
    try:
        proposal = _seed_proposal(app)
        reviewer, csrf, _ = _client(app, AdminRole.REVIEWER)
        review = _review(reviewer, csrf, proposal.id, decision=decision)
        review_id = UUID(review.json()["proposal_review_decision_id"])

        wrong_review = _materialize(
            reviewer,
            csrf,
            proposal.id,
            uuid4(),
        )
        negative = _materialize(
            reviewer,
            csrf,
            proposal.id,
            review_id,
        )

        assert wrong_review.status_code == 409
        assert wrong_review.json()["code"] == "ADMIN_FEED_ITEM_REVIEW_MISMATCH"
        assert negative.status_code == 409
        assert negative.json()["code"] == (
            "ADMIN_FEED_ITEM_REVIEW_NOT_ACCEPTED"
        )
        assert app.state.ingestion_orchestration_repository.find_materialization(
            proposal.id,
            target_kind="NORMALIZED_ARTIFACT",
        ) is None
    finally:
        get_settings.cache_clear()


def test_unreviewed_missing_and_wrong_schema_errors_are_bounded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _app(monkeypatch)
    try:
        reviewer, csrf, _ = _client(app, AdminRole.REVIEWER)
        unreviewed = _seed_proposal(app)
        unreviewed_response = _materialize(
            reviewer,
            csrf,
            unreviewed.id,
            uuid4(),
        )
        missing = _materialize(
            reviewer,
            csrf,
            uuid4(),
            uuid4(),
        )

        wrong_kind = _seed_proposal(
            app,
            proposal_kind="CLAIM",
            schema_ref="kefe.claim",
        )
        review = _review(reviewer, csrf, wrong_kind.id)
        wrong_kind_response = _materialize(
            reviewer,
            csrf,
            wrong_kind.id,
            UUID(review.json()["proposal_review_decision_id"]),
        )

        assert unreviewed_response.status_code == 409
        assert unreviewed_response.json()["code"] == (
            "ADMIN_FEED_ITEM_REVIEW_REQUIRED"
        )
        assert missing.status_code == 404
        assert missing.json()["code"] == "ADMIN_FEED_ITEM_PROPOSAL_NOT_FOUND"
        assert wrong_kind_response.status_code == 422
        assert wrong_kind_response.json()["code"] == (
            "ADMIN_FEED_ITEM_PROPOSAL_SCHEMA_INVALID"
        )
        assert "payload" not in repr(wrong_kind_response.json()).lower()
    finally:
        get_settings.cache_clear()
