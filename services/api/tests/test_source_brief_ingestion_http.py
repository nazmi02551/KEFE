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
from kefe_api.modules.ingestion_orchestration.feed_item_extraction import (
    PIPELINE_CODE as FEED_PIPELINE_CODE,
)
from kefe_api.modules.ingestion_orchestration.feed_item_extraction import (
    PIPELINE_VERSION as FEED_PIPELINE_VERSION,
)
from kefe_api.modules.ingestion_orchestration.feed_item_extraction import (
    PROPOSAL_KIND as FEED_ITEM_KIND,
)
from kefe_api.modules.ingestion_orchestration.feed_item_extraction import (
    RISK_CODE as FEED_ITEM_RISK,
)
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
    PIPELINE_CODE,
    PIPELINE_VERSION,
    SOURCE_BRIEF_KIND,
    SOURCE_BRIEF_RISK_CODE,
    SOURCE_BRIEF_SCHEMA_REF,
    SOURCE_BRIEF_SCHEMA_VERSION,
    STAGE_CODE,
    STAGE_VERSION,
    require_source_brief_normalized_artifact,
)
from kefe_api.modules.knowledge.models import SourceArtifact
from kefe_api.modules.knowledge.source_evidence import (
    canonical_content_hash,
    canonical_storage_ref,
)

SOURCE_AT = datetime(2026, 8, 3, 10, 0, tzinfo=UTC)


def _app(monkeypatch: pytest.MonkeyPatch, *, version: str = "0.22.0"):
    monkeypatch.setenv("KEFE_PERSISTENCE_BACKEND", "memory")
    monkeypatch.setenv("KEFE_API_VERSION", version)
    get_settings.cache_clear()
    return create_app()


def _admin(app, role: AdminRole) -> tuple[TestClient, str]:
    subject_id = uuid4()
    app.state.admin_session_store.upsert_subject(
        subject_id,
        roles=frozenset({role}),
    )
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


def _seed_feed_item(app) -> tuple[UUID, UUID, SourceArtifact]:
    body = b"source-brief-feed-evidence"
    content_hash = canonical_content_hash(body)
    source = app.state.knowledge_repository.add_source_artifact(
        SourceArtifact.create(
            adapter_code="test.source_brief_feed.v1",
            external_locator="https://example.test/feed.xml",
            captured_at=SOURCE_AT,
            content_hash=content_hash,
            canonical_url="https://example.test/feed.xml",
            publisher_or_issuer="Example News",
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
        configuration_hash="sha256:feed-config-source-brief",
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
        output_hash="sha256:feed-item-output-source-brief",
        started_at=SOURCE_AT,
        completed_at=SOURCE_AT + timedelta(seconds=1),
        outcome=StageOutcome.SUCCEEDED,
    )
    payload = {
        "source_artifact_id": str(source.id),
        "feed_content_hash": source.content_hash,
        "feed_storage_ref": source.raw_storage_ref,
        "feed_format": "RSS_2_0",
        "feed_title": "Example News",
        "item_id": "item-source-brief-1",
        "item_title": "A bounded feed item title",
        "item_url": "https://example.test/items/1",
        "published_at": "2026-08-03T09:30:00+00:00",
        "summary_text": "A deterministic bounded summary.",
    }
    proposal = Proposal(
        id=UUID(int=1551),
        proposal_kind=FEED_ITEM_KIND,
        payload_schema_ref=PAYLOAD_SCHEMA_REF,
        payload_schema_version=PAYLOAD_SCHEMA_VERSION,
        payload=payload,
        payload_hash=stable_payload_hash(payload),
        run_id=run.id,
        stage_execution_id=execution.id,
        created_at=SOURCE_AT + timedelta(seconds=2),
        configuration_version=run.configuration_hash,
        risk_code=FEED_ITEM_RISK,
        provenance_ref=source.raw_storage_ref,
    )
    repository.complete_successful_stage(execution, (proposal,))
    parent = repository.get_run(run.id)
    assert parent is not None
    repository.update_run(parent.transition(IngestionRunState.SUCCEEDED))
    return run.id, proposal.id, source


def _accept(client: TestClient, csrf: str, proposal_id: UUID) -> None:
    response = client.post(
        f"/internal/admin/v1/proposals/{proposal_id}/review",
        headers={ADMIN_CSRF_HEADER: csrf},
        json={"decision": "ACCEPTED", "policy_version": "feed-accept-v1"},
    )
    assert response.status_code == 201


def test_source_brief_command_is_022_only_authorized_and_idempotent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    old_app = _app(monkeypatch, version="0.21.0")
    old_reviewer, old_csrf = _admin(old_app, AdminRole.REVIEWER)
    assert old_reviewer.post(
        "/internal/admin/v1/feed-items/00000000-0000-0000-0000-000000000001/source-brief",
        headers={ADMIN_CSRF_HEADER: old_csrf},
    ).status_code == 404

    app = _app(monkeypatch)
    try:
        _parent_run_id, proposal_id, source = _seed_feed_item(app)
        reviewer, csrf = _admin(app, AdminRole.REVIEWER)
        editor, editor_csrf = _admin(app, AdminRole.EDITOR)

        csrf_missing = reviewer.post(
            f"/internal/admin/v1/feed-items/{proposal_id}/source-brief"
        )
        assert csrf_missing.status_code == 403
        assert csrf_missing.json()["code"] == "ADMIN_CSRF_REQUIRED"

        forbidden = editor.post(
            f"/internal/admin/v1/feed-items/{proposal_id}/source-brief",
            headers={ADMIN_CSRF_HEADER: editor_csrf},
        )
        assert forbidden.status_code == 403
        assert forbidden.json()["code"] == "ADMIN_FORBIDDEN"

        before_review = reviewer.post(
            f"/internal/admin/v1/feed-items/{proposal_id}/source-brief",
            headers={ADMIN_CSRF_HEADER: csrf},
        )
        assert before_review.status_code == 409
        assert before_review.json()["code"] == "ADMIN_SOURCE_BRIEF_REVIEW_REQUIRED"

        _accept(reviewer, csrf, proposal_id)
        first = reviewer.post(
            f"/internal/admin/v1/feed-items/{proposal_id}/source-brief",
            headers={ADMIN_CSRF_HEADER: csrf},
        )
        assert first.status_code == 200
        first_body = first.json()
        assert first_body["run_state"] == "SUCCEEDED"
        assert first_body["proposal_review_state"] == "PENDING"

        second = reviewer.post(
            f"/internal/admin/v1/feed-items/{proposal_id}/source-brief",
            headers={ADMIN_CSRF_HEADER: csrf},
        )
        assert second.status_code == 200
        assert second.json() == first_body

        normalized_id = UUID(first_body["normalized_artifact_id"])
        run_id = UUID(first_body["run_id"])
        brief_id = UUID(first_body["source_brief_proposal_id"])
        normalized = app.state.knowledge_repository.get_normalized_artifact(
            normalized_id
        )
        assert normalized is not None
        metadata = require_source_brief_normalized_artifact(normalized)
        assert metadata.parent_feed_item_proposal_id == proposal_id
        assert metadata.source_artifact_id == source.id
        assert normalized.text == "A deterministic bounded summary."

        repository = app.state.ingestion_orchestration_repository
        run = repository.get_run(run_id)
        assert run is not None
        assert run.state is IngestionRunState.SUCCEEDED
        assert run.input_artifact_kind is InputArtifactKind.NORMALIZED_ARTIFACT
        assert run.input_artifact_id == normalized_id
        assert run.input_content_hash == normalized.content_hash
        assert run.pipeline_code == PIPELINE_CODE
        assert run.pipeline_version == PIPELINE_VERSION

        history = repository.list_stage_executions(run_id)
        assert len(history) == 1
        assert history[0].stage_code == STAGE_CODE
        assert history[0].stage_version == STAGE_VERSION
        assert history[0].outcome is StageOutcome.SUCCEEDED

        proposals = repository.list_proposals(run_id)
        assert len(proposals) == 1
        brief = proposals[0]
        assert brief.id == brief_id
        assert brief.proposal_kind == SOURCE_BRIEF_KIND
        assert brief.payload_schema_ref == SOURCE_BRIEF_SCHEMA_REF
        assert brief.payload_schema_version == SOURCE_BRIEF_SCHEMA_VERSION
        assert brief.risk_code == SOURCE_BRIEF_RISK_CODE
        assert brief.payload["parent_feed_item_proposal_id"] == str(proposal_id)
        assert brief.payload["normalized_artifact_id"] == str(normalized_id)
        assert brief.payload["source_artifact_id"] == str(source.id)
        assert brief.payload["evidence_ref"] == source.raw_storage_ref
        assert repository.get_review_decision(brief.id) is None
        assert repository.find_materialization(brief.id) is None
        assert len(repository.list_proposals(run_id)) == 1
    finally:
        get_settings.cache_clear()
