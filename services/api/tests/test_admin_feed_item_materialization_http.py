from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

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
from kefe_api.modules.knowledge.models import (
    ArtifactKind,
    NormalizedArtifact,
    SourceArtifact,
)
from kefe_api.modules.knowledge.source_evidence import (
    canonical_content_hash,
    canonical_storage_ref,
)


class FixedProposalProcessor:
    def __init__(self, proposal: ProposalDraft) -> None:
        self._proposal = proposal

    def process(self, **_) -> StageProcessorResult:
        return StageProcessorResult(
            proposals=(self._proposal,),
            output_metadata={"fixture": "admin-feed-item-materialization"},
        )


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


def _seed(
    app,
    *,
    proposal_kind: str = "FEED_ITEM",
    payload_schema_ref: str = "kefe.feed-item",
    payload_schema_version: str = "1.0.0",
    risk_code: str | None = "UNREVIEWED_EXTERNAL_FEED_ITEM",
):
    knowledge = app.state.knowledge_repository
    orchestration = app.state.ingestion_orchestration_service
    repository = app.state.ingestion_orchestration_repository
    content_hash = canonical_content_hash(f"admin-feed-{uuid4()}".encode())
    source = knowledge.add_source_artifact(
        SourceArtifact.create(
            adapter_code="test.admin.rss.v1",
            external_locator=f"https://feeds.example.test/{uuid4()}.xml",
            captured_at=datetime(2026, 8, 3, 5, 30, tzinfo=UTC),
            content_hash=content_hash,
            publisher_or_issuer="Admin Feed",
            language_code="en",
            jurisdiction_code="GB",
            raw_storage_ref=canonical_storage_ref(content_hash),
        )
    )
    if proposal_kind == "FEED_ITEM":
        payload: dict[str, object] = {
            "source_artifact_id": str(source.id),
            "feed_content_hash": source.content_hash,
            "feed_storage_ref": source.raw_storage_ref,
            "feed_format": "RSS_2_0",
            "feed_title": "Admin Feed",
            "item_id": f"urn:admin:item:{uuid4()}",
            "item_title": "Admin reviewed feed item",
            "item_url": "https://news.example.test/admin-item",
            "published_at": "2026-08-03T05:20:00+00:00",
            "summary_text": "An explicitly reviewed feed item.",
        }
        provenance_ref = source.raw_storage_ref
    else:
        payload = {"normalized_text": "Unsupported proposal", "language_code": "en"}
        provenance_ref = "fixture:unsupported"

    run = orchestration.start_run(
        input_artifact_kind=InputArtifactKind.SOURCE_ARTIFACT,
        input_artifact_id=source.id,
        input_content_hash=source.content_hash,
        pipeline_code=f"ADMIN_FEED_MATERIALIZATION_{uuid4()}",
        pipeline_version="1.0.0",
        configuration_hash=f"sha256:admin-feed-{uuid4()}",
        locale="en-GB",
        jurisdiction_code="GB",
    )
    orchestration.execute_stage(
        run_id=run.id,
        stage_code="PROPOSE",
        stage_version="1.0.0",
        input_hash=source.content_hash,
        max_attempts=1,
        executor_kind=ExecutorKind.DETERMINISTIC,
        processor=FixedProposalProcessor(
            ProposalDraft(
                proposal_kind=proposal_kind,
                payload_schema_ref=payload_schema_ref,
                payload_schema_version=payload_schema_version,
                payload=payload,
                configuration_version="admin-feed-materialization-v1",
                risk_code=risk_code,
                provenance_ref=provenance_ref,
            )
        ),
    )
    return source, repository.list_proposals(run.id)[0]


def _review(
    client: TestClient,
    csrf: str,
    proposal_id: UUID,
    decision: ProposalReviewDecisionKind,
) -> dict[str, object]:
    response = client.post(
        f"/internal/admin/v1/proposals/{proposal_id}/review",
        headers={ADMIN_CSRF_HEADER: csrf},
        json={
            "decision": decision.value,
            "rationale": "Explicit Admin fixture review.",
            "reason_code": "EDITORIAL_SOURCE_CHECKED",
            "policy_version": "proposal-review-v1",
            "risk_policy_version": "external-content-risk-v1",
        },
    )
    assert response.status_code == 201
    return response.json()


def _materialize(
    client: TestClient,
    csrf: str | None,
    proposal_id: UUID,
    review_id: UUID,
):
    headers = {ADMIN_CSRF_HEADER: csrf} if csrf is not None else {}
    return client.post(
        f"/internal/admin/v1/proposals/{proposal_id}/feed-item-materialization",
        headers=headers,
        json={"proposal_review_decision_id": str(review_id)},
    )


def test_command_requires_auth_csrf_and_both_reviewer_capabilities(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _app(monkeypatch)
    try:
        _, proposal = _seed(app)
        anonymous = TestClient(app)
        editor, editor_csrf = _admin(app, AdminRole.EDITOR)
        publisher, publisher_csrf = _admin(app, AdminRole.PUBLISHER)
        reviewer, reviewer_csrf = _admin(app, AdminRole.REVIEWER)
        random_review_id = uuid4()

        unauthenticated = _materialize(
            anonymous,
            "not-valid",
            proposal.id,
            random_review_id,
        )
        editor_forbidden = _materialize(
            editor,
            editor_csrf,
            proposal.id,
            random_review_id,
        )
        publisher_forbidden = _materialize(
            publisher,
            publisher_csrf,
            proposal.id,
            random_review_id,
        )
        csrf_required = _materialize(
            reviewer,
            None,
            proposal.id,
            random_review_id,
        )
        review_required = _materialize(
            reviewer,
            reviewer_csrf,
            proposal.id,
            random_review_id,
        )

        assert unauthenticated.status_code == 401
        assert unauthenticated.json()["code"] == "ADMIN_AUTH_REQUIRED"
        assert editor_forbidden.status_code == 403
        assert editor_forbidden.json()["code"] == "ADMIN_FORBIDDEN"
        assert publisher_forbidden.status_code == 403
        assert publisher_forbidden.json()["code"] == "ADMIN_FORBIDDEN"
        assert csrf_required.status_code == 403
        assert csrf_required.json()["code"] == "ADMIN_CSRF_REQUIRED"
        assert review_required.status_code == 409
        assert review_required.json()["code"] == (
            "INGESTION_PROPOSAL_REVIEW_NOT_ACCEPTED"
        )
    finally:
        get_settings.cache_clear()


def test_accepted_command_is_bounded_idempotent_and_persists_exact_target(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _app(monkeypatch)
    try:
        source, proposal = _seed(app)
        reviewer, csrf = _admin(app, AdminRole.REVIEWER)
        review = _review(
            reviewer,
            csrf,
            proposal.id,
            ProposalReviewDecisionKind.ACCEPTED,
        )
        review_id = UUID(review["proposal_review_decision_id"])

        wrong_binding = _materialize(
            reviewer,
            csrf,
            proposal.id,
            uuid4(),
        )
        first = _materialize(
            reviewer,
            csrf,
            proposal.id,
            review_id,
        )
        replay = _materialize(
            reviewer,
            csrf,
            proposal.id,
            review_id,
        )

        assert wrong_binding.status_code == 409
        assert wrong_binding.json()["code"] == (
            "INGESTION_PROPOSAL_REVIEW_BINDING_MISMATCH"
        )
        assert first.status_code == 200
        assert replay.status_code == 200
        assert replay.json() == first.json()
        body = first.json()
        assert set(body) == {
            "proposal_materialization_id",
            "proposal_id",
            "proposal_review_decision_id",
            "target_kind",
            "target_id",
            "materialized_at",
        }
        assert body["proposal_id"] == str(proposal.id)
        assert body["proposal_review_decision_id"] == str(review_id)
        assert body["target_kind"] == "NORMALIZED_ARTIFACT"
        expected_target_id = uuid5(
            NAMESPACE_URL,
            f"kefe:proposal:{proposal.id}:NORMALIZED_ARTIFACT",
        )
        assert body["target_id"] == str(expected_target_id)
        assert "payload" not in body
        assert "feed_storage_ref" not in body
        assert "evidence" not in body

        artifact = app.state.knowledge_repository.get_normalized_artifact(
            expected_target_id
        )
        assert artifact is not None
        assert artifact.source_artifact_id == source.id
        assert artifact.artifact_kind is ArtifactKind.EXTERNAL_EVIDENCE
        materializations = [
            item
            for item in (
                app.state.ingestion_orchestration_repository.find_materialization(
                    proposal.id,
                    target_kind="NORMALIZED_ARTIFACT",
                ),
            )
            if item is not None
        ]
        assert len(materializations) == 1
    finally:
        get_settings.cache_clear()


def test_rejected_unsupported_and_conflicting_commands_fail_bounded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _app(monkeypatch)
    try:
        _, rejected_proposal = _seed(app)
        reviewer, csrf = _admin(app, AdminRole.REVIEWER)
        rejected_review = _review(
            reviewer,
            csrf,
            rejected_proposal.id,
            ProposalReviewDecisionKind.REJECTED,
        )
        rejected = _materialize(
            reviewer,
            csrf,
            rejected_proposal.id,
            UUID(rejected_review["proposal_review_decision_id"]),
        )
        assert rejected.status_code == 409
        assert rejected.json()["code"] == "INGESTION_PROPOSAL_REVIEW_NOT_ACCEPTED"

        _, unsupported_proposal = _seed(
            app,
            proposal_kind="CLAIM",
            payload_schema_ref="knowledge/claim",
            payload_schema_version="1",
            risk_code=None,
        )
        unsupported_review = _review(
            reviewer,
            csrf,
            unsupported_proposal.id,
            ProposalReviewDecisionKind.ACCEPTED,
        )
        unsupported = _materialize(
            reviewer,
            csrf,
            unsupported_proposal.id,
            UUID(unsupported_review["proposal_review_decision_id"]),
        )
        assert unsupported.status_code == 422
        assert unsupported.json()["code"] == (
            "INGESTION_FEED_ITEM_MATERIALIZATION_UNSUPPORTED"
        )

        source, conflict_proposal = _seed(app)
        conflict_review = _review(
            reviewer,
            csrf,
            conflict_proposal.id,
            ProposalReviewDecisionKind.ACCEPTED,
        )
        target_id = uuid5(
            NAMESPACE_URL,
            f"kefe:proposal:{conflict_proposal.id}:NORMALIZED_ARTIFACT",
        )
        app.state.knowledge_repository.add_normalized_artifact(
            NormalizedArtifact(
                id=target_id,
                source_artifact_id=source.id,
                artifact_kind=ArtifactKind.EXTERNAL_EVIDENCE,
                normalized_at=datetime(2026, 8, 3, 5, 45, tzinfo=UTC),
                content_hash="sha256:http-conflict",
                text="Conflicting HTTP artifact",
                language_code=source.language_code,
                jurisdiction_code=source.jurisdiction_code,
                media_metadata={"conflict": True},
            )
        )
        conflict = _materialize(
            reviewer,
            csrf,
            conflict_proposal.id,
            UUID(conflict_review["proposal_review_decision_id"]),
        )
        assert conflict.status_code == 409
        assert conflict.json()["code"] == (
            "INGESTION_FEED_ITEM_MATERIALIZATION_CONFLICT"
        )
    finally:
        get_settings.cache_clear()
