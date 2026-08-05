from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from kefe_api.core.settings import get_settings
from kefe_api.main import create_app
from kefe_api.modules.admin_security.router import ADMIN_SESSION_COOKIE
from kefe_api.modules.ingestion_orchestration.models import (
    ExecutorKind,
    IngestionRun,
    IngestionRunState,
    InputArtifactKind,
    Proposal,
    ProposalReviewDecision,
    ProposalReviewDecisionKind,
    StageExecution,
    StageOutcome,
    stable_payload_hash,
)

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)

ENDPOINT = "/internal/admin/v1/operational-reports/snapshot"


def _seed_subject(database_url: str) -> UUID:
    subject_id = uuid4()
    now = datetime.now(UTC)
    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(
            text("INSERT INTO admin_security.subject (id, state) VALUES (:id, 'ACTIVE')"),
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
            {"id": uuid4(), "subject_id": subject_id, "granted_at": now},
        )
    return subject_id


def _admin_client(app, subject_id: UUID) -> TestClient:
    now = datetime.now(UTC)
    issued = app.state.admin_session_store.issue(
        admin_subject_id=subject_id,
        authenticated_at=now,
        mfa_satisfied_at=now,
        expires_at=now + timedelta(hours=12),
    )
    client = TestClient(app)
    client.cookies.set(ADMIN_SESSION_COOKIE, issued.session_token)
    return client


def _seed_editorial_states(database_url: str) -> None:
    engine = create_engine(database_url)
    now = datetime.now(UTC)
    states = (
        "DRAFT",
        "IN_REVIEW",
        "APPROVED",
        "PUBLISHED",
        "SUPERSEDED",
        "WITHDRAWN",
    )
    with engine.begin() as connection:
        for state in states:
            case_id = uuid4()
            connection.execute(
                text(
                    """
                    INSERT INTO editorial.case_item (id, slug, created_at)
                    VALUES (:id, :slug, :created_at)
                    """
                ),
                {
                    "id": case_id,
                    "slug": f"operational-{state.lower()}-{case_id.hex}",
                    "created_at": now,
                },
            )
            connection.execute(
                text(
                    """
                    INSERT INTO editorial.case_version (
                        id, case_id, version_no, lifecycle_state, aggregate,
                        created_at, updated_at, published_at
                    ) VALUES (
                        :id, :case_id, 1, :state, '{}'::jsonb,
                        :created_at, :created_at, :published_at
                    )
                    """
                ),
                {
                    "id": uuid4(),
                    "case_id": case_id,
                    "state": state,
                    "created_at": now,
                    "published_at": now if state == "PUBLISHED" else None,
                },
            )


def _seed_proposal(app, decision: ProposalReviewDecisionKind | None) -> None:
    repository = app.state.ingestion_orchestration_repository
    now = datetime.now(UTC)
    run_id = uuid4()
    stage_id = uuid4()
    proposal_id = uuid4()
    repository.create_or_get_run(
        IngestionRun(
            id=run_id,
            run_key=f"operational-pg-{run_id}",
            input_artifact_kind=InputArtifactKind.SOURCE_ARTIFACT,
            input_artifact_id=uuid4(),
            input_content_hash="a" * 64,
            pipeline_code="OPERATIONAL_REPORT_PG",
            pipeline_version="1",
            configuration_hash="b" * 64,
            state=IngestionRunState.RUNNING,
            created_at=now,
            updated_at=now,
        )
    )
    repository.add_stage_execution(
        StageExecution(
            id=stage_id,
            run_id=run_id,
            stage_code="PROPOSE",
            stage_version="1",
            attempt_no=1,
            max_attempts=1,
            executor_kind=ExecutorKind.DETERMINISTIC,
            input_hash="c" * 64,
            started_at=now,
            outcome=StageOutcome.SUCCEEDED,
            output_hash="d" * 64,
            completed_at=now,
        )
    )
    payload = {"state": decision.value if decision else "PENDING"}
    repository.add_proposal(
        Proposal(
            id=proposal_id,
            proposal_kind="CASE_CANDIDATE",
            payload_schema_ref="urn:kefe:test:operational-report-pg",
            payload_schema_version="1",
            payload=payload,
            payload_hash=stable_payload_hash(payload),
            run_id=run_id,
            stage_execution_id=stage_id,
            created_at=now,
            risk_code="L0",
        )
    )
    if decision is not None:
        repository.add_review_decision(
            ProposalReviewDecision(
                id=uuid4(),
                proposal_id=proposal_id,
                decision=decision,
                reviewer_ref="test:pg-reviewer",
                decided_at=now,
            )
        )


def _seed_reason(database_url: str, state: str, *, reported: bool) -> None:
    engine = create_engine(database_url)
    now = datetime.now(UTC) - timedelta(minutes=5)
    author_id = uuid4()
    reporter_id = uuid4()
    case_id = uuid4()
    version_id = uuid4()
    session_id = uuid4()
    reason_id = uuid4()
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO identity.actor (id, actor_kind, state, created_at)
                VALUES
                    (:author, 'GUEST', 'ACTIVE', :now),
                    (:reporter, 'GUEST', 'ACTIVE', :now)
                """
            ),
            {"author": author_id, "reporter": reporter_id, "now": now},
        )
        connection.execute(
            text(
                """
                INSERT INTO content.case_item (
                    id, slug, base_format_code, primary_domain_code,
                    lifecycle_state, content_risk, created_at, updated_at
                ) VALUES (
                    :id, :slug, 'DILEMMA', 'DAILY_LIFE',
                    'PUBLISHED', 'L0', :now, :now
                )
                """
            ),
            {
                "id": case_id,
                "slug": f"operational-reason-{case_id.hex}",
                "now": now,
            },
        )
        connection.execute(
            text(
                """
                INSERT INTO content.case_version (
                    id, case_id, version_no, status, title, summary,
                    accepts_weighs, published_at, created_at,
                    base_format_code, primary_domain_code, content_risk
                ) VALUES (
                    :id, :case_id, 1, 'PUBLISHED', 'Operational reason',
                    'Aggregate-only fixture', true, :now, :now,
                    'DILEMMA', 'DAILY_LIFE', 'L0'
                )
                """
            ),
            {"id": version_id, "case_id": case_id, "now": now},
        )
        connection.execute(
            text(
                """
                INSERT INTO decision.weigh_session (
                    id, actor_id, case_id, case_version_id, state,
                    commit_idempotency_key, started_at, committed_at,
                    created_at, updated_at
                ) VALUES (
                    :id, :actor, :case_id, :version_id, 'COMMITTED',
                    :key, :now, :now, :now, :now
                )
                """
            ),
            {
                "id": session_id,
                "actor": author_id,
                "case_id": case_id,
                "version_id": version_id,
                "key": f"operational-{session_id}",
                "now": now,
            },
        )
        connection.execute(
            text(
                """
                INSERT INTO community.reason (
                    id, actor_id, session_id, case_version_id, tags, body,
                    moderation_state, created_at, updated_at
                ) VALUES (
                    :id, :actor, :session, :version,
                    '["FAIRNESS"]'::jsonb, :body, :state, :now, :now
                )
                """
            ),
            {
                "id": reason_id,
                "actor": author_id,
                "session": session_id,
                "version": version_id,
                "body": "Pending aggregate fixture" if state == "PENDING" else None,
                "state": state,
                "now": now,
            },
        )
        if reported:
            connection.execute(
                text(
                    """
                    INSERT INTO community.reason_report (
                        id, reason_id, reporter_actor_id, report_code, created_at
                    ) VALUES (:id, :reason, :reporter, 'PERSONAL_DATA', :created_at)
                    """
                ),
                {
                    "id": uuid4(),
                    "reason": reason_id,
                    "reporter": reporter_id,
                    "created_at": now + timedelta(minutes=1),
                },
            )


def test_postgres_operational_report_aggregates_survive_restart(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = os.environ["KEFE_DATABASE_URL"]
    monkeypatch.setenv("KEFE_PERSISTENCE_BACKEND", "postgres")
    get_settings.cache_clear()
    reviewer_subject = _seed_subject(database_url)
    _seed_editorial_states(database_url)

    try:
        first_app = create_app()
        _seed_proposal(first_app, None)
        _seed_proposal(first_app, ProposalReviewDecisionKind.ACCEPTED)
        _seed_proposal(first_app, ProposalReviewDecisionKind.REJECTED)
        _seed_proposal(first_app, ProposalReviewDecisionKind.CHANGES_REQUESTED)
        _seed_reason(database_url, "PENDING", reported=False)
        _seed_reason(database_url, "NOT_REQUIRED", reported=True)
        _seed_reason(database_url, "BLOCKED", reported=True)

        first = _admin_client(first_app, reviewer_subject).get(ENDPOINT)
        assert first.status_code == 200
        first_body = first.json()
        assert first_body["editorial_lifecycle"] == {
            "DRAFT": 1,
            "IN_REVIEW": 1,
            "APPROVED": 1,
            "PUBLISHED": 1,
            "SUPERSEDED": 1,
            "WITHDRAWN": 1,
        }
        assert first_body["proposal_review"] == {
            "PENDING": 1,
            "ACCEPTED": 1,
            "REJECTED": 1,
            "CHANGES_REQUESTED": 1,
        }
        assert first_body["moderation"] == {"PENDING": 1, "REPORTED": 1}
        assert first_body["as_of"] == first_body["content_supply"]["as_of"]

        second_app = create_app()
        second = _admin_client(second_app, reviewer_subject).get(ENDPOINT)
        assert second.status_code == 200
        second_body = second.json()
        for section in ("editorial_lifecycle", "proposal_review", "moderation"):
            assert second_body[section] == first_body[section]

        engine = create_engine(database_url)
        with engine.connect() as connection:
            report_tables = connection.execute(
                text(
                    """
                    SELECT count(*)
                    FROM information_schema.tables
                    WHERE table_schema IN ('public', 'editorial', 'community')
                      AND table_name LIKE '%operational_report%'
                    """
                )
            ).scalar_one()
            reason_moderation_audit = connection.execute(
                text("SELECT count(*) FROM community.reason_moderation_audit")
            ).scalar_one()
        assert int(report_tables) == 0
        assert int(reason_moderation_audit) == 0
    finally:
        get_settings.cache_clear()
