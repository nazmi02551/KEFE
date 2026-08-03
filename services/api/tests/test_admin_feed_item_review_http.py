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
    PIPELINE_CODE,
    PIPELINE_VERSION,
    PROPOSAL_KIND,
    RISK_CODE,
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
from kefe_api.modules.knowledge.models import SourceArtifact
from kefe_api.modules.knowledge.source_evidence import (
    canonical_content_hash,
    canonical_storage_ref,
)

NOW = datetime(2026, 8, 3, 10, 0, tzinfo=UTC)
BODY = b"<rss><channel><title>Fixture</title></channel></rss>"


def _app(monkeypatch: pytest.MonkeyPatch, *, version: str = "0.21.0"):
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
    issued = app.state.admin_session_store.issue(
        admin_subject_id=subject_id,
        authenticated_at=NOW,
        mfa_satisfied_at=NOW,
        expires_at=NOW + timedelta(hours=1),
    )
    client = TestClient(app)
    client.cookies.set(ADMIN_SESSION_COOKIE, issued.session_token)
    return client, issued.csrf_token


def _payload(source: SourceArtifact, *, item_id: str, item_title: str) -> dict[str, object]:
    return {
        "source_artifact_id": str(source.id),
        "feed_content_hash": source.content_hash,
        "feed_storage_ref": source.raw_storage_ref,
        "feed_format": "RSS_2_0",
        "feed_title": "Example News",
        "item_id": item_id,
        "item_title": item_title,
        "item_url": f"https://example.test/items/{item_id}",
        "published_at": "2026-08-03T09:30:00+00:00",
        "summary_text": f"Summary for {item_title}.",
    }


def _seed_feed_items(app) -> tuple[UUID, tuple[UUID, ...], SourceArtifact]:
    content_hash = canonical_content_hash(BODY)
    source = app.state.knowledge_repository.add_source_artifact(
        SourceArtifact.create(
            adapter_code="test.feed_items.v1",
            external_locator="https://example.test/feed.xml",
            captured_at=NOW,
            content_hash=content_hash,
            canonical_url="https://example.test/feed.xml",
            publisher_or_issuer="Example News",
            raw_storage_ref=canonical_storage_ref(content_hash),
        )
    )
    service = app.state.ingestion_orchestration_service
    repository = app.state.ingestion_orchestration_repository
    run = service.start_run(
        input_artifact_kind=InputArtifactKind.SOURCE_ARTIFACT,
        input_artifact_id=source.id,
        input_content_hash=source.content_hash,
        pipeline_code=PIPELINE_CODE,
        pipeline_version=PIPELINE_VERSION,
        configuration_hash="sha256:feed-item-config",
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
        output_hash="sha256:feed-items-output",
        started_at=NOW,
        completed_at=NOW + timedelta(seconds=1),
        outcome=StageOutcome.SUCCEEDED,
    )
    proposals: list[Proposal] = []
    for index, item_id, item_title in (
        (1, "item-a", "First feed item"),
        (2, "item-b", "Second feed item"),
    ):
        payload = _payload(source, item_id=item_id, item_title=item_title)
        proposals.append(
            Proposal(
                id=UUID(int=500 + index),
                proposal_kind=PROPOSAL_KIND,
                payload_schema_ref=PAYLOAD_SCHEMA_REF,
                payload_schema_version=PAYLOAD_SCHEMA_VERSION,
                payload=payload,
                payload_hash=stable_payload_hash(payload),
                run_id=run.id,
                stage_execution_id=execution.id,
                created_at=NOW + timedelta(seconds=index),
                configuration_version=run.configuration_hash,
                risk_code=RISK_CODE,
                provenance_ref=source.raw_storage_ref,
            )
        )
    repository.complete_successful_stage(execution, tuple(proposals))
    return run.id, tuple(item.id for item in proposals), source


def test_surface_is_additive_at_021_and_authorized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    old_app = _app(monkeypatch, version="0.20.0")
    old_reviewer, _ = _admin(old_app, AdminRole.REVIEWER)
    assert old_reviewer.get("/internal/admin/v1/feed-items").status_code == 404

    app = _app(monkeypatch)
    try:
        run_id, proposal_ids, _source = _seed_feed_items(app)
        reviewer, csrf = _admin(app, AdminRole.REVIEWER)
        editor, _ = _admin(app, AdminRole.EDITOR)

        forbidden = editor.get("/internal/admin/v1/feed-items")
        assert forbidden.status_code == 403
        assert forbidden.json()["code"] == "ADMIN_FORBIDDEN"

        first = reviewer.get(
            "/internal/admin/v1/feed-items",
            params={"limit": 1, "run_id": str(run_id)},
        )
        assert first.status_code == 200
        body = first.json()
        assert [item["proposal_id"] for item in body["items"]] == [
            str(proposal_ids[0])
        ]
        assert body["items"][0]["item_title"] == "First feed item"
        assert "summary_text" not in body["items"][0]
        assert "evidence_ref" not in body["items"][0]
        assert body["next_cursor"]

        second = reviewer.get(
            "/internal/admin/v1/feed-items",
            params={
                "limit": 1,
                "run_id": str(run_id),
                "cursor": body["next_cursor"],
            },
        )
        assert [item["proposal_id"] for item in second.json()["items"]] == [
            str(proposal_ids[1])
        ]

        detail = reviewer.get(
            f"/internal/admin/v1/feed-items/{proposal_ids[0]}"
        )
        assert detail.status_code == 200
        detail_body = detail.json()
        assert detail_body["summary_text"] == "Summary for First feed item."
        assert detail_body["evidence_ref"].startswith("evidence://sha256/")
        assert detail_body["feed_content_hash"].startswith("sha256:")
        assert "payload" not in detail_body

        reviewed = reviewer.post(
            f"/internal/admin/v1/proposals/{proposal_ids[0]}/review",
            headers={ADMIN_CSRF_HEADER: csrf},
            json={
                "decision": "ACCEPTED",
                "policy_version": "feed-review-v1",
            },
        )
        assert reviewed.status_code == 201
        accepted = reviewer.get(
            "/internal/admin/v1/feed-items",
            params={"review_state": "ACCEPTED", "run_id": str(run_id)},
        )
        assert [item["proposal_id"] for item in accepted.json()["items"]] == [
            str(proposal_ids[0])
        ]
    finally:
        get_settings.cache_clear()


def test_detail_hides_other_kinds_and_rejects_contract_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _app(monkeypatch)
    try:
        run_id, proposal_ids, source = _seed_feed_items(app)
        reviewer, _ = _admin(app, AdminRole.REVIEWER)
        repository = app.state.ingestion_orchestration_repository
        run = repository.get_run(run_id)
        assert run is not None
        execution = repository.list_stage_executions(run_id)[0]

        other_payload = {"title": "Not a feed item"}
        other = Proposal(
            id=UUID(int=900),
            proposal_kind="QUESTION_DRAFT",
            payload_schema_ref="kefe.question-draft",
            payload_schema_version="1.0.0",
            payload=other_payload,
            payload_hash=stable_payload_hash(other_payload),
            run_id=run_id,
            stage_execution_id=execution.id,
            created_at=NOW + timedelta(minutes=1),
            configuration_version=run.configuration_hash,
            risk_code="L0",
        )
        repository.add_proposal(other)
        hidden = reviewer.get(f"/internal/admin/v1/feed-items/{other.id}")
        assert hidden.status_code == 404
        assert hidden.json()["code"] == "ADMIN_FEED_ITEM_NOT_FOUND"

        drift_payload = _payload(source, item_id="drift", item_title="Drifted")
        drift_payload["raw_body"] = "must-never-cross"
        drift = Proposal(
            id=UUID(int=901),
            proposal_kind=PROPOSAL_KIND,
            payload_schema_ref=PAYLOAD_SCHEMA_REF,
            payload_schema_version=PAYLOAD_SCHEMA_VERSION,
            payload=drift_payload,
            payload_hash=stable_payload_hash(drift_payload),
            run_id=run_id,
            stage_execution_id=execution.id,
            created_at=NOW + timedelta(minutes=2),
            configuration_version=run.configuration_hash,
            risk_code=RISK_CODE,
            provenance_ref=source.raw_storage_ref,
        )
        repository.add_proposal(drift)
        invalid = reviewer.get(f"/internal/admin/v1/feed-items/{drift.id}")
        assert invalid.status_code == 409
        assert invalid.json()["code"] == "ADMIN_FEED_ITEM_CONTRACT_INVALID"
        assert "must-never-cross" not in invalid.text

        valid = reviewer.get(f"/internal/admin/v1/feed-items/{proposal_ids[0]}")
        assert valid.status_code == 200
    finally:
        get_settings.cache_clear()
