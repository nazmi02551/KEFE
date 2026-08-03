from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from kefe_api.core.settings import get_settings
from kefe_api.main import create_app
from kefe_api.modules.admin_security.router import ADMIN_CSRF_HEADER, ADMIN_SESSION_COOKIE
from kefe_api.modules.ingestion_orchestration.feed_item_extraction import (
    PAYLOAD_SCHEMA_REF,
    PAYLOAD_SCHEMA_VERSION,
    PIPELINE_CODE as FEED_PIPELINE_CODE,
    PIPELINE_VERSION as FEED_PIPELINE_VERSION,
    PROPOSAL_KIND as FEED_ITEM_KIND,
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
    SOURCE_BRIEF_KIND,
    STAGE_CODE,
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


def _subject(database_url: str) -> object:
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


def _client(app, subject_id) -> tuple[TestClient, str]:
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


def _seed(app) -> tuple[object, SourceArtifact]:
    body = f"postgres-source-brief-{uuid4()}".encode()
    content_hash = canonical_content_hash(body)
    source = app.state.knowledge_repository.add_source_artifact(
        SourceArtifact.create(
            adapter_code="test.postgres_source_brief.v1",
            external_locator=f"https://example.test/feed/{uuid4()}.xml",
            captured_at=SOURCE_AT,
            content_hash=content_hash,
            canonical_url="https://example.test/feed.xml",
            publisher_or_issuer="PostgreSQL News",
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
        configuration_hash=f"sha256:postgres-feed-{uuid4()}",
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
        started_at=SOURCE_AT,
        completed_at=SOURCE_AT + timedelta(seconds=1),
        outcome=StageOutcome.SUCCEEDED,
    )
    payload = {
        "source_artifact_id": str(source.id),
        "feed_content_hash": source.content_hash,
        "feed_storage_ref": source.raw_storage_ref,
        "feed_format": "ATOM_1_0",
        "feed_title": "PostgreSQL News",
        "item_id": f"urn:postgres:brief:{uuid4()}",
        "item_title": "PostgreSQL source brief title",
        "item_url": "https://example.test/postgres/source-brief",
        "published_at": "2026-08-03T10:20:00+00:00",
        "summary_text": "PostgreSQL deterministic source brief summary.",
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
    repository.update_run(
        repository.get_run(run.id).transition(IngestionRunState.SUCCEEDED)
    )
    return proposal.id, source


def test_postgres_source_brief_command_is_durable_and_idempotent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = os.environ["KEFE_DATABASE_URL"]
    monkeypatch.setenv("KEFE_PERSISTENCE_BACKEND", "postgres")
    monkeypatch.setenv("KEFE_API_VERSION", "0.22.0")
    get_settings.cache_clear()
    reviewer_id = _subject(database_url)
    try:
        app = create_app()
        proposal_id, source = _seed(app)
        reviewer, csrf = _client(app, reviewer_id)
        accepted = reviewer.post(
            f"/internal/admin/v1/proposals/{proposal_id}/review",
            headers={ADMIN_CSRF_HEADER: csrf},
            json={"decision": "ACCEPTED", "policy_version": "postgres-feed-v1"},
        )
        assert accepted.status_code == 201

        first = reviewer.post(
            f"/internal/admin/v1/feed-items/{proposal_id}/source-brief",
            headers={ADMIN_CSRF_HEADER: csrf},
        )
        assert first.status_code == 200
        second = reviewer.post(
            f"/internal/admin/v1/feed-items/{proposal_id}/source-brief",
            headers={ADMIN_CSRF_HEADER: csrf},
        )
        assert second.status_code == 200
        assert second.json() == first.json()

        body = first.json()
        normalized_id = body["normalized_artifact_id"]
        run_id = body["run_id"]
        brief_id = body["source_brief_proposal_id"]
        assert body["run_state"] == "SUCCEEDED"

        engine = create_engine(database_url)
        with engine.connect() as connection:
            normalized_count = connection.execute(
                text(
                    "SELECT count(*) FROM knowledge.normalized_artifact "
                    "WHERE id = CAST(:id AS uuid)"
                ),
                {"id": normalized_id},
            ).scalar_one()
            materialization_count = connection.execute(
                text(
                    """
                    SELECT count(*) FROM ingestion.proposal_materialization
                    WHERE proposal_id = CAST(:proposal_id AS uuid)
                      AND target_kind = 'NORMALIZED_ARTIFACT'
                    """
                ),
                {"proposal_id": str(proposal_id)},
            ).scalar_one()
            run_row = connection.execute(
                text(
                    """
                    SELECT state, normalized_artifact_id, pipeline_code
                    FROM ingestion.ingestion_run
                    WHERE id = CAST(:id AS uuid)
                    """
                ),
                {"id": run_id},
            ).mappings().one()
            stage_count = connection.execute(
                text(
                    """
                    SELECT count(*) FROM ingestion.stage_execution
                    WHERE run_id = CAST(:run_id AS uuid)
                      AND stage_code = :stage_code
                    """
                ),
                {"run_id": run_id, "stage_code": STAGE_CODE},
            ).scalar_one()
            proposal_row = connection.execute(
                text(
                    """
                    SELECT proposal_kind, payload, risk_code
                    FROM ingestion.proposal
                    WHERE id = CAST(:id AS uuid)
                    """
                ),
                {"id": brief_id},
            ).mappings().one()
            review_count = connection.execute(
                text(
                    """
                    SELECT count(*) FROM ingestion.proposal_review_decision
                    WHERE proposal_id = CAST(:id AS uuid)
                    """
                ),
                {"id": brief_id},
            ).scalar_one()

        assert normalized_count == 1
        assert materialization_count == 1
        assert run_row["state"] == "SUCCEEDED"
        assert str(run_row["normalized_artifact_id"]) == normalized_id
        assert run_row["pipeline_code"] == PIPELINE_CODE
        assert stage_count == 1
        assert proposal_row["proposal_kind"] == SOURCE_BRIEF_KIND
        assert proposal_row["payload"]["source_artifact_id"] == str(source.id)
        assert proposal_row["payload"]["evidence_ref"] == source.raw_storage_ref
        assert review_count == 0
    finally:
        get_settings.cache_clear()
