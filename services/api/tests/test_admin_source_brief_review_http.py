from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from kefe_api.core.settings import get_settings
from kefe_api.main import create_app
from kefe_api.modules.admin_security.models import AdminRole
from kefe_api.modules.admin_security.router import ADMIN_CSRF_HEADER, ADMIN_SESSION_COOKIE
from kefe_api.modules.ingestion_orchestration.feed_item_extraction import (
    PAYLOAD_SCHEMA_REF,
    PAYLOAD_SCHEMA_VERSION,
)
from kefe_api.modules.ingestion_orchestration.feed_item_extraction import PIPELINE_CODE as FEED_PIPELINE_CODE
from kefe_api.modules.ingestion_orchestration.feed_item_extraction import PIPELINE_VERSION as FEED_PIPELINE_VERSION
from kefe_api.modules.ingestion_orchestration.feed_item_extraction import PROPOSAL_KIND as FEED_ITEM_KIND
from kefe_api.modules.ingestion_orchestration.feed_item_extraction import RISK_CODE as FEED_ITEM_RISK
from kefe_api.modules.ingestion_orchestration.models import (
    ExecutorKind,
    IngestionRunState,
    InputArtifactKind,
    Proposal,
    StageExecution,
    StageOutcome,
    stable_payload_hash,
)
from kefe_api.modules.ingestion_orchestration.source_brief_ingestion import (
    CONFIGURATION_HASH,
    SOURCE_BRIEF_KIND,
    SOURCE_BRIEF_RISK_CODE,
    SOURCE_BRIEF_SCHEMA_REF,
    SOURCE_BRIEF_SCHEMA_VERSION,
)
from kefe_api.modules.knowledge.models import SourceArtifact
from kefe_api.modules.knowledge.source_evidence import canonical_content_hash, canonical_storage_ref

SOURCE_AT = datetime(2026, 8, 3, 10, 0, tzinfo=UTC)


def _app(monkeypatch: pytest.MonkeyPatch, *, version: str = "0.23.0"):
    monkeypatch.setenv("KEFE_PERSISTENCE_BACKEND", "memory")
    monkeypatch.setenv("KEFE_API_VERSION", version)
    get_settings.cache_clear()
    return create_app()


def _admin(app, role: AdminRole) -> tuple[TestClient, str]:
    subject_id = uuid4()
    app.state.admin_session_store.upsert_subject(subject_id, roles=frozenset({role}))
    issued_at = datetime.now(UTC)
    issued = app.state.admin_session_store.issue(
        admin_subject_id=subject_id,
        authenticated_at=issued_at,
        mfa_satisfied_at=issued_at,
        expires_at=issued_at + timedelta(hours=1),
    )
    client = TestClient(app)
    client.cookies.set(ADMIN_SESSION_COOKIE, issued.session_token)
    return client, issued.csrf_token


def _seed_feed_item(app, *, index: int) -> tuple[UUID, SourceArtifact]:
    body = f"source-brief-review-evidence-{index}".encode()
    content_hash = canonical_content_hash(body)
    source = app.state.knowledge_repository.add_source_artifact(
        SourceArtifact.create(
            adapter_code="test.source_brief_review.v1",
            external_locator=f"https://example.test/feed-{index}.xml",
            captured_at=SOURCE_AT + timedelta(minutes=index),
            content_hash=content_hash,
            canonical_url=f"https://example.test/feed-{index}.xml",
            publisher_or_issuer="Example Review News",
            language_code="tr",
            jurisdiction_code="TR",
            raw_storage_ref=canonical_storage_ref(content_hash),
        )
    )
    service = app.state.ingestion_orchestration_service
    repository = app.state.ingestion_orchestration_repository
    run = service.start_run(
        input_artifact_kind=InputArtifactKind.SOURCE_ARTIFACT,
        input_artifact_id=source.id,
        input_content_hash=source.content_hash,
        pipeline_code=FEED_PIPELINE_CODE,
        pipeline_version=FEED_PIPELINE_VERSION,
        configuration_hash=f"sha256:feed-review-{index}",
        locale="tr-TR",
        jurisdiction_code="TR",
    )
    repository.update_run(run.transition(IngestionRunState.RUNNING))
    execution = StageExecution(
        id=uuid4(),
        run_id=run.id,
        stage_code="EXTRACT_FEED_ITEMS",
        stage_version="1.0.0",
        attempt_no=1,
        max_attempts=3,
        executor_kind=ExecutorKind.DETERMINISTIC,
        input_hash=source.content_hash,
        output_hash=f"sha256:feed-review-output-{index}",
        started_at=SOURCE_AT + timedelta(minutes=index),
        completed_at=SOURCE_AT + timedelta(minutes=index, seconds=1),
        outcome=StageOutcome.SUCCEEDED,
    )
    payload = {
        "source_artifact_id": str(source.id),
        "feed_content_hash": source.content_hash,
        "feed_storage_ref": source.raw_storage_ref,
        "feed_format": "RSS_2_0" if index == 1 else "ATOM_1_0",
        "feed_title": "Example Review News",
        "item_id": f"item-review-{index}",
        "item_title": f"Source Brief review headline {index}",
        "item_url": f"https://example.test/items/review-{index}",
        "published_at": f"2026-08-03T09:3{index}:00+00:00",
        "summary_text": f"Typed Source Brief synopsis {index}.",
    }
    proposal = Proposal(
        id=UUID(int=5600 + index),
        proposal_kind=FEED_ITEM_KIND,
        payload_schema_ref=PAYLOAD_SCHEMA_REF,
        payload_schema_version=PAYLOAD_SCHEMA_VERSION,
        payload=payload,
        payload_hash=stable_payload_hash(payload),
        run_id=run.id,
        stage_execution_id=execution.id,
        created_at=SOURCE_AT + timedelta(minutes=index, seconds=2),
        configuration_version=run.configuration_hash,
        risk_code=FEED_ITEM_RISK,
        provenance_ref=source.raw_storage_ref,
    )
    repository.complete_successful_stage(execution, (proposal,))
    parent = repository.get_run(run.id)
    assert parent is not None
    repository.update_run(parent.transition(IngestionRunState.SUCCEEDED))
    return proposal.id, source


def _accept_and_build(client: TestClient, csrf: str, proposal_id: UUID) -> UUID:
    accepted = client.post(
        f"/internal/admin/v1/proposals/{proposal_id}/review",
        headers={ADMIN_CSRF_HEADER: csrf},
        json={"decision": "ACCEPTED", "policy_version": "brief-review-v1"},
    )
    assert accepted.status_code == 201
    built = client.post(
        f"/internal/admin/v1/feed-items/{proposal_id}/source-brief",
        headers={ADMIN_CSRF_HEADER: csrf},
    )
    assert built.status_code == 200
    return UUID(built.json()["source_brief_proposal_id"])


def test_source_brief_review_surface_is_023_typed_and_refreshes_review(monkeypatch: pytest.MonkeyPatch) -> None:
    old_app = _app(monkeypatch, version="0.22.0")
    old_reviewer, _ = _admin(old_app, AdminRole.REVIEWER)
    assert old_reviewer.get("/internal/admin/v1/source-briefs").status_code == 404

    app = _app(monkeypatch)
    try:
        parent_one, source_one = _seed_feed_item(app, index=1)
        parent_two, _source_two = _seed_feed_item(app, index=2)
        reviewer, csrf = _admin(app, AdminRole.REVIEWER)
        editor, _ = _admin(app, AdminRole.EDITOR)
        brief_one = _accept_and_build(reviewer, csrf, parent_one)
        brief_two = _accept_and_build(reviewer, csrf, parent_two)

        forbidden = editor.get("/internal/admin/v1/source-briefs")
        assert forbidden.status_code == 403
        assert forbidden.json()["code"] == "ADMIN_FORBIDDEN"

        first = reviewer.get("/internal/admin/v1/source-briefs", params={"limit": 1})
        assert first.status_code == 200
        first_body = first.json()
        assert len(first_body["items"]) == 1
        assert first_body["next_cursor"]
        assert "synopsis" not in first_body["items"][0]
        assert "evidence_ref" not in first_body["items"][0]

        second = reviewer.get(
            "/internal/admin/v1/source-briefs",
            params={"limit": 1, "cursor": first_body["next_cursor"]},
        )
        returned = {
            UUID(first_body["items"][0]["proposal_id"]),
            UUID(second.json()["items"][0]["proposal_id"]),
        }
        assert returned == {brief_one, brief_two}

        detail = reviewer.get(f"/internal/admin/v1/source-briefs/{brief_one}")
        assert detail.status_code == 200
        detail_body = detail.json()
        assert detail_body["parent_feed_item_proposal_id"] == str(parent_one)
        assert detail_body["source_artifact_id"] == str(source_one.id)
        assert detail_body["headline"] == "Source Brief review headline 1"
        assert detail_body["synopsis"] == "Typed Source Brief synopsis 1."
        assert detail_body["source_feed_title"] == "Example Review News"
        assert detail_body["source_item_id"] == "item-review-1"
        assert detail_body["evidence_ref"] == source_one.raw_storage_ref
        assert "payload" not in detail_body

        reviewed = reviewer.post(
            f"/internal/admin/v1/proposals/{brief_one}/review",
            headers={ADMIN_CSRF_HEADER: csrf},
            json={"decision": "ACCEPTED", "policy_version": "brief-accept-v1"},
        )
        assert reviewed.status_code == 201
        accepted = reviewer.get("/internal/admin/v1/source-briefs", params={"review_state": "ACCEPTED"})
        assert [item["proposal_id"] for item in accepted.json()["items"]] == [str(brief_one)]
        accepted_detail = reviewer.get(f"/internal/admin/v1/source-briefs/{brief_one}")
        assert accepted_detail.json()["review_state"] == "ACCEPTED"
        assert accepted_detail.json()["review"] is not None
    finally:
        get_settings.cache_clear()


def test_source_brief_detail_hides_other_kind_and_rejects_payload_drift(monkeypatch: pytest.MonkeyPatch) -> None:
    app = _app(monkeypatch)
    try:
        parent_id, _source = _seed_feed_item(app, index=1)
        reviewer, csrf = _admin(app, AdminRole.REVIEWER)
        brief_id = _accept_and_build(reviewer, csrf, parent_id)

        hidden = reviewer.get(f"/internal/admin/v1/source-briefs/{parent_id}")
        assert hidden.status_code == 404
        assert hidden.json()["code"] == "ADMIN_SOURCE_BRIEF_NOT_FOUND"

        repository = app.state.ingestion_orchestration_repository
        original = repository.get_proposal(brief_id)
        assert original is not None
        drift_payload = dict(original.payload)
        drift_payload["raw_body"] = "must-never-cross"
        drift = Proposal(
            id=UUID(int=5699),
            proposal_kind=SOURCE_BRIEF_KIND,
            payload_schema_ref=SOURCE_BRIEF_SCHEMA_REF,
            payload_schema_version=SOURCE_BRIEF_SCHEMA_VERSION,
            payload=drift_payload,
            payload_hash=stable_payload_hash(drift_payload),
            run_id=original.run_id,
            stage_execution_id=original.stage_execution_id,
            created_at=original.created_at + timedelta(seconds=1),
            configuration_version=CONFIGURATION_HASH,
            risk_code=SOURCE_BRIEF_RISK_CODE,
            provenance_ref=original.provenance_ref,
        )
        repository.add_proposal(drift)
        invalid = reviewer.get(f"/internal/admin/v1/source-briefs/{drift.id}")
        assert invalid.status_code == 409
        assert invalid.json()["code"] == "ADMIN_SOURCE_BRIEF_CONTRACT_INVALID"
        assert "must-never-cross" not in invalid.text
        assert reviewer.get(f"/internal/admin/v1/source-briefs/{brief_id}").status_code == 200
    finally:
        get_settings.cache_clear()
