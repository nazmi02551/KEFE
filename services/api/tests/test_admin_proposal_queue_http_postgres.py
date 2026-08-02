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

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)


def _seed_subject(database_url: str, role: str) -> UUID:
    subject_id = uuid4()
    now = datetime.now(UTC)
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
                "granted_at": now,
            },
        )
    return subject_id


def _client(app, subject_id: UUID) -> tuple[TestClient, str]:
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


def _seed_proposals(app, database_url: str) -> tuple[str, UUID, tuple[UUID, ...]]:
    engine = create_engine(database_url)
    source = PostgresKnowledgeRepository(engine).add_source_artifact(
        SourceArtifact.create(
            adapter_code="admin-proposal-queue-fixture",
            external_locator=f"https://example.test/proposal-queue/{uuid4()}",
            content_hash=f"sha256:proposal-queue-{uuid4()}",
            language_code="tr",
        )
    )
    pipeline_code = f"ADMIN_QUEUE_{uuid4().hex[:10]}"
    service = app.state.ingestion_orchestration_service
    repository = app.state.ingestion_orchestration_repository
    run = service.start_run(
        input_artifact_kind=InputArtifactKind.SOURCE_ARTIFACT,
        input_artifact_id=source.id,
        input_content_hash=source.content_hash,
        pipeline_code=pipeline_code,
        pipeline_version="1.0.0",
        configuration_hash="sha256:admin-queue-config",
        taxonomy_version="taxonomy-v1",
        methodology_version="methodology-v1",
        locale="tr-TR",
        jurisdiction_code="TR",
    )
    repository.update_run(run.transition(IngestionRunState.RUNNING))
    base = datetime(2026, 8, 2, 4, 0, tzinfo=UTC)
    execution = StageExecution(
        id=uuid4(),
        run_id=run.id,
        stage_code="QUEUE_PROPOSALS",
        stage_version="1",
        attempt_no=1,
        max_attempts=1,
        executor_kind=ExecutorKind.DETERMINISTIC,
        input_hash="sha256:admin-queue-input",
        output_hash="sha256:admin-queue-output",
        started_at=base,
        completed_at=base + timedelta(seconds=1),
        outcome=StageOutcome.SUCCEEDED,
    )
    proposals: list[Proposal] = []
    for index, kind, risk in (
        (1, "QUESTION_DRAFT", "L0"),
        (2, "DECISION_PROBLEM", "L1"),
        (3, "QUESTION_DRAFT", "L1"),
    ):
        proposal_id = uuid4()
        payload = {"title": f"PostgreSQL queue {index}", "secret": f"pg-{index}"}
        proposals.append(
            Proposal(
                id=proposal_id,
                proposal_kind=kind,
                payload_schema_ref=f"kefe.{kind.lower()}",
                payload_schema_version="1.0.0",
                payload=payload,
                payload_hash=stable_payload_hash(payload),
                run_id=run.id,
                stage_execution_id=execution.id,
                created_at=base + timedelta(seconds=index),
                taxonomy_version="taxonomy-v1",
                configuration_version="configuration-v1",
                methodology_version="methodology-v1",
                confidence=0.9,
                risk_code=risk,
                provenance_ref=f"postgres-queue:{index}",
            )
        )
    repository.complete_successful_stage(execution, tuple(proposals))
    return pipeline_code, run.id, tuple(item.id for item in proposals)


def test_postgres_admin_proposal_queue_paginates_filters_and_refreshes_review(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = os.environ["KEFE_DATABASE_URL"]
    monkeypatch.setenv("KEFE_PERSISTENCE_BACKEND", "postgres")
    get_settings.cache_clear()
    reviewer_id = _seed_subject(database_url, "REVIEWER")
    try:
        app = create_app()
        pipeline_code, run_id, proposal_ids = _seed_proposals(app, database_url)
        reviewer, csrf = _client(app, reviewer_id)

        first = reviewer.get(
            "/internal/admin/v1/proposals",
            params={"pipeline_code": pipeline_code, "limit": 2},
        )
        assert first.status_code == 200
        body = first.json()
        assert [item["proposal_id"] for item in body["items"]] == [
            str(proposal_ids[0]),
            str(proposal_ids[1]),
        ]
        assert all("payload" not in item for item in body["items"])
        assert body["next_cursor"]

        second = reviewer.get(
            "/internal/admin/v1/proposals",
            params={
                "pipeline_code": pipeline_code,
                "limit": 2,
                "cursor": body["next_cursor"],
            },
        )
        assert second.status_code == 200
        assert [item["proposal_id"] for item in second.json()["items"]] == [
            str(proposal_ids[2])
        ]

        filtered = reviewer.get(
            "/internal/admin/v1/proposals",
            params={
                "pipeline_code": pipeline_code,
                "review_state": "PENDING",
                "proposal_kind": "QUESTION_DRAFT",
                "risk_code": "L1",
                "run_id": str(run_id),
            },
        )
        assert [item["proposal_id"] for item in filtered.json()["items"]] == [
            str(proposal_ids[2])
        ]

        detail = reviewer.get(f"/internal/admin/v1/proposals/{proposal_ids[2]}")
        assert detail.status_code == 200
        assert detail.json()["payload"]["secret"] == "pg-3"

        reviewed = reviewer.post(
            f"/internal/admin/v1/proposals/{proposal_ids[2]}/review",
            headers={ADMIN_CSRF_HEADER: csrf},
            json={"decision": "ACCEPTED", "policy_version": "review-v1"},
        )
        assert reviewed.status_code == 201
        accepted = reviewer.get(
            "/internal/admin/v1/proposals",
            params={
                "pipeline_code": pipeline_code,
                "review_state": "ACCEPTED",
            },
        )
        assert [item["proposal_id"] for item in accepted.json()["items"]] == [
            str(proposal_ids[2])
        ]
        assert accepted.json()["items"][0]["review"]["reviewer_ref"] == (
            f"admin:{reviewer_id}"
        )

        invalid = reviewer.get(
            "/internal/admin/v1/proposals",
            params={"pipeline_code": pipeline_code, "cursor": "broken"},
        )
        assert invalid.status_code == 422
        assert invalid.json()["code"] == "ADMIN_PROPOSAL_QUEUE_CURSOR_INVALID"
    finally:
        get_settings.cache_clear()
