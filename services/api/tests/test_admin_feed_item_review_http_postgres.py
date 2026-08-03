from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from kefe_api.core.settings import get_settings
from kefe_api.infrastructure.postgres_knowledge import PostgresKnowledgeRepository
from kefe_api.main import create_app
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

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)

NOW = datetime(2026, 8, 3, 10, 30, tzinfo=UTC)


def _seed_subject(database_url: str, role: str) -> UUID:
    subject_id = uuid4()
    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO admin_security.subject (id, state)
                VALUES (:subject_id, 'ACTIVE')
                """
            ),
            {"subject_id": subject_id},
        )
        connection.execute(
            text(
                """
                INSERT INTO admin_security.role_assignment (
                    id, subject_id, role, granted_at
                ) VALUES (:id, :subject_id, :role, :granted_at)
                """
            ),
            {
                "id": uuid4(),
                "subject_id": subject_id,
                "role": role,
                "granted_at": NOW,
            },
        )
    return subject_id


def _client(app, subject_id: UUID) -> tuple[TestClient, str]:
    issued = app.state.admin_session_store.issue(
        admin_subject_id=subject_id,
        authenticated_at=NOW,
        mfa_satisfied_at=NOW,
        expires_at=NOW + timedelta(hours=1),
    )
    client = TestClient(app)
    client.cookies.set(ADMIN_SESSION_COOKIE, issued.session_token)
    return client, issued.csrf_token


def _seed_feed_items(app, database_url: str) -> tuple[UUID, tuple[UUID, ...]]:
    body = f"postgres-feed-{uuid4()}".encode()
    content_hash = canonical_content_hash(body)
    engine = create_engine(database_url)
    source = PostgresKnowledgeRepository(engine).add_source_artifact(
        SourceArtifact.create(
            adapter_code="test.postgres_feed.v1",
            external_locator=f"https://example.test/feed/{uuid4()}.xml",
            captured_at=NOW,
            content_hash=content_hash,
            canonical_url="https://example.test/feed.xml",
            publisher_or_issuer="PostgreSQL Feed",
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
        configuration_hash="sha256:postgres-feed-config",
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
        output_hash=f"sha256:postgres-feed-output-{uuid4()}",
        started_at=NOW,
        completed_at=NOW + timedelta(seconds=1),
        outcome=StageOutcome.SUCCEEDED,
    )
    proposals: list[Proposal] = []
    for index in (1, 2):
        payload = {
            "source_artifact_id": str(source.id),
            "feed_content_hash": source.content_hash,
            "feed_storage_ref": source.raw_storage_ref,
            "feed_format": "ATOM_1_0",
            "feed_title": "PostgreSQL Feed",
            "item_id": f"urn:postgres:item:{index}",
            "item_title": f"PostgreSQL item {index}",
            "item_url": f"https://example.test/postgres/{index}",
            "published_at": f"2026-08-03T10:0{index}:00+00:00",
            "summary_text": f"PostgreSQL summary {index}.",
        }
        proposals.append(
            Proposal(
                id=uuid4(),
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
    return run.id, tuple(item.id for item in proposals)


def test_postgres_feed_item_review_list_detail_and_review_refresh(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = os.environ["KEFE_DATABASE_URL"]
    monkeypatch.setenv("KEFE_PERSISTENCE_BACKEND", "postgres")
    monkeypatch.setenv("KEFE_API_VERSION", "0.21.0")
    get_settings.cache_clear()
    reviewer_id = _seed_subject(database_url, "REVIEWER")
    try:
        app = create_app()
        run_id, proposal_ids = _seed_feed_items(app, database_url)
        reviewer, csrf = _client(app, reviewer_id)

        first = reviewer.get(
            "/internal/admin/v1/feed-items",
            params={"run_id": str(run_id), "limit": 1},
        )
        assert first.status_code == 200
        first_body = first.json()
        assert [item["proposal_id"] for item in first_body["items"]] == [
            str(proposal_ids[0])
        ]
        assert first_body["next_cursor"]

        second = reviewer.get(
            "/internal/admin/v1/feed-items",
            params={
                "run_id": str(run_id),
                "limit": 1,
                "cursor": first_body["next_cursor"],
            },
        )
        assert [item["proposal_id"] for item in second.json()["items"]] == [
            str(proposal_ids[1])
        ]

        detail = reviewer.get(
            f"/internal/admin/v1/feed-items/{proposal_ids[1]}"
        )
        assert detail.status_code == 200
        assert detail.json()["item_title"] == "PostgreSQL item 2"
        assert detail.json()["feed_format"] == "ATOM_1_0"
        assert detail.json()["evidence_ref"].startswith("evidence://sha256/")
        assert "payload" not in detail.json()

        reviewed = reviewer.post(
            f"/internal/admin/v1/proposals/{proposal_ids[1]}/review",
            headers={ADMIN_CSRF_HEADER: csrf},
            json={
                "decision": "ACCEPTED",
                "policy_version": "postgres-feed-review-v1",
            },
        )
        assert reviewed.status_code == 201
        accepted = reviewer.get(
            "/internal/admin/v1/feed-items",
            params={"review_state": "ACCEPTED", "run_id": str(run_id)},
        )
        assert [item["proposal_id"] for item in accepted.json()["items"]] == [
            str(proposal_ids[1])
        ]
        accepted_detail = reviewer.get(
            f"/internal/admin/v1/feed-items/{proposal_ids[1]}"
        )
        assert accepted_detail.json()["review_state"] == "ACCEPTED"
        assert accepted_detail.json()["review"]["reviewer_ref"] == (
            f"admin:{reviewer_id}"
        )
    finally:
        get_settings.cache_clear()
