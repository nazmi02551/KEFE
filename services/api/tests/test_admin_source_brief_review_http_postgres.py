from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from kefe_api.core.settings import get_settings
from kefe_api.main import create_app
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
from kefe_api.modules.knowledge.models import SourceArtifact
from kefe_api.modules.knowledge.source_evidence import (
    canonical_content_hash,
    canonical_storage_ref,
)

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)

SOURCE_AT = datetime(2026, 8, 3, 10, 30, tzinfo=UTC)


def _subject(database_url: str) -> UUID:
    subject_id = uuid4()
    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO admin_security.subject (id, state) "
                "VALUES (:id, 'ACTIVE')"
            ),
            {"id": subject_id},
        )
        connection.execute(
            text(
                """
                INSERT INTO admin_security.role_assignment (
                    id, subject_id, role, granted_at
                ) VALUES (:id, :subject_id, 'REVIEWER', :granted_at)
                """
            ),
            {
                "id": uuid4(),
                "subject_id": subject_id,
                "granted_at": SOURCE_AT,
            },
        )
    return subject_id


def _client(app, subject_id: UUID) -> tuple[TestClient, str]:
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


def _seed_feed_item(app) -> tuple[UUID, SourceArtifact]:
    body = f"postgres-source-brief-review-{uuid4()}".encode()
    content_hash = canonical_content_hash(body)
    source = app.state.knowledge_repository.add_source_artifact(
        SourceArtifact.create(
            adapter_code="test.postgres_source_brief_review.v1",
            external_locator=f"https://example.test/feed/{uuid4()}.xml",
            captured_at=SOURCE_AT,
            content_hash=content_hash,
            canonical_url="https://example.test/feed.xml",
            publisher_or_issuer="PostgreSQL Review News",
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
        configuration_hash=f"sha256:postgres-review-{uuid4()}",
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
        output_hash=f"sha256:postgres-review-output-{uuid4()}",
        started_at=SOURCE_AT,
        completed_at=SOURCE_AT + timedelta(seconds=1),
        outcome=StageOutcome.SUCCEEDED,
    )
    payload = {
        "source_artifact_id": str(source.id),
        "feed_content_hash": source.content_hash,
        "feed_storage_ref": source.raw_storage_ref,
        "feed_format": "ATOM_1_0",
        "feed_title": "PostgreSQL Review News",
        "item_id": f"urn:postgres:review:{uuid4()}",
        "item_title": "PostgreSQL Source Brief review headline",
        "item_url": "https://example.test/postgres/review-source-brief",
        "published_at": "2026-08-03T10:20:00+00:00",
        "summary_text": "PostgreSQL typed Source Brief synopsis.",
    }
    proposal = Proposal(
        id=uuid4(),
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
    return proposal.id, source


def test_postgres_source_brief_review_list_detail_and_review_refresh(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = os.environ["KEFE_DATABASE_URL"]
    monkeypatch.setenv("KEFE_PERSISTENCE_BACKEND", "postgres")
    monkeypatch.setenv("KEFE_API_VERSION", "0.23.0")
    get_settings.cache_clear()
    reviewer_id = _subject(database_url)
    try:
        app = create_app()
        parent_id, source = _seed_feed_item(app)
        reviewer, csrf = _client(app, reviewer_id)
        accepted_parent = reviewer.post(
            f"/internal/admin/v1/proposals/{parent_id}/review",
            headers={ADMIN_CSRF_HEADER: csrf},
            json={"decision": "ACCEPTED", "policy_version": "postgres-parent-v1"},
        )
        assert accepted_parent.status_code == 201
        built = reviewer.post(
            f"/internal/admin/v1/feed-items/{parent_id}/source-brief",
            headers={ADMIN_CSRF_HEADER: csrf},
        )
        assert built.status_code == 200
        brief_id = built.json()["source_brief_proposal_id"]
        run_id = built.json()["run_id"]

        listed = reviewer.get(
            "/internal/admin/v1/source-briefs",
            params={"run_id": run_id},
        )
        assert listed.status_code == 200
        assert [item["proposal_id"] for item in listed.json()["items"]] == [
            brief_id
        ]
        assert "synopsis" not in listed.json()["items"][0]
        assert "evidence_ref" not in listed.json()["items"][0]

        detail = reviewer.get(f"/internal/admin/v1/source-briefs/{brief_id}")
        assert detail.status_code == 200
        detail_body = detail.json()
        assert detail_body["parent_feed_item_proposal_id"] == str(parent_id)
        assert detail_body["source_artifact_id"] == str(source.id)
        assert detail_body["headline"] == (
            "PostgreSQL Source Brief review headline"
        )
        assert detail_body["synopsis"] == (
            "PostgreSQL typed Source Brief synopsis."
        )
        assert detail_body["evidence_ref"] == source.raw_storage_ref
        assert "payload" not in detail_body

        reviewed = reviewer.post(
            f"/internal/admin/v1/proposals/{brief_id}/review",
            headers={ADMIN_CSRF_HEADER: csrf},
            json={"decision": "ACCEPTED", "policy_version": "postgres-brief-v1"},
        )
        assert reviewed.status_code == 201
        accepted = reviewer.get(
            "/internal/admin/v1/source-briefs",
            params={"review_state": "ACCEPTED", "run_id": run_id},
        )
        assert [item["proposal_id"] for item in accepted.json()["items"]] == [
            brief_id
        ]
        refreshed = reviewer.get(
            f"/internal/admin/v1/source-briefs/{brief_id}"
        )
        assert refreshed.json()["review_state"] == "ACCEPTED"
        assert refreshed.json()["review"]["reviewer_ref"] == (
            f"admin:{reviewer_id}"
        )
    finally:
        get_settings.cache_clear()
