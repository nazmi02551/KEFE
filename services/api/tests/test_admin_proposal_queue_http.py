from __future__ import annotations

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
    IngestionRunState,
    InputArtifactKind,
    Proposal,
    StageExecution,
    StageOutcome,
    stable_payload_hash,
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


def _seed_run(
    app,
    *,
    pipeline_code: str,
    proposal_specs: tuple[tuple[int, str, str | None], ...],
) -> tuple[UUID, tuple[UUID, ...]]:
    service = app.state.ingestion_orchestration_service
    repository = app.state.ingestion_orchestration_repository
    run = service.start_run(
        input_artifact_kind=InputArtifactKind.SOURCE_ARTIFACT,
        input_artifact_id=uuid4(),
        input_content_hash=f"sha256:{pipeline_code}:{uuid4()}",
        pipeline_code=pipeline_code,
        pipeline_version="1.0.0",
        configuration_hash="sha256:proposal-queue-config",
        taxonomy_version="taxonomy-v1",
        methodology_version="methodology-v1",
        locale="tr-TR",
        jurisdiction_code="TR",
    )
    repository.update_run(run.transition(IngestionRunState.RUNNING))
    base = datetime(2026, 8, 2, 3, 0, tzinfo=UTC)
    execution = StageExecution(
        id=uuid4(),
        run_id=run.id,
        stage_code="PROPOSAL_BATCH",
        stage_version="1",
        attempt_no=1,
        max_attempts=1,
        executor_kind=ExecutorKind.DETERMINISTIC,
        input_hash=f"sha256:{pipeline_code}:input",
        output_hash=f"sha256:{pipeline_code}:output",
        started_at=base,
        completed_at=base + timedelta(seconds=1),
        outcome=StageOutcome.SUCCEEDED,
    )
    proposals: list[Proposal] = []
    for index, proposal_kind, risk_code in proposal_specs:
        proposal_id = UUID(int=index)
        payload = {"title": f"Proposal {index}", "secret": f"payload-{index}"}
        proposals.append(
            Proposal(
                id=proposal_id,
                proposal_kind=proposal_kind,
                payload_schema_ref=f"kefe.{proposal_kind.lower()}",
                payload_schema_version="1.0.0",
                payload=payload,
                payload_hash=stable_payload_hash(payload),
                run_id=run.id,
                stage_execution_id=execution.id,
                created_at=base + timedelta(seconds=index),
                taxonomy_version="taxonomy-v1",
                configuration_version="configuration-v1",
                methodology_version="methodology-v1",
                confidence=0.8,
                risk_code=risk_code,
                provenance_ref=f"fixture:{index}",
            )
        )
    repository.complete_successful_stage(execution, tuple(proposals))
    return run.id, tuple(proposal.id for proposal in proposals)


def test_queue_is_authorized_keyset_paginated_and_list_excludes_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _app(monkeypatch)
    try:
        _run_id, proposal_ids = _seed_run(
            app,
            pipeline_code="TODAY_RADAR",
            proposal_specs=(
                (101, "QUESTION_DRAFT", "L0"),
                (102, "DECISION_PROBLEM", "L1"),
                (103, "CANDIDATE_CASE", "L1"),
            ),
        )
        reviewer, _ = _admin(app, AdminRole.REVIEWER)
        editor, _ = _admin(app, AdminRole.EDITOR)

        forbidden = editor.get("/internal/admin/v1/proposals")
        first = reviewer.get("/internal/admin/v1/proposals", params={"limit": 2})

        assert forbidden.status_code == 403
        assert forbidden.json()["code"] == "ADMIN_FORBIDDEN"
        assert first.status_code == 200
        first_body = first.json()
        assert [item["proposal_id"] for item in first_body["items"]] == [
            str(proposal_ids[0]),
            str(proposal_ids[1]),
        ]
        assert all("payload" not in item for item in first_body["items"])
        assert first_body["next_cursor"]

        second = reviewer.get(
            "/internal/admin/v1/proposals",
            params={"limit": 2, "cursor": first_body["next_cursor"]},
        )
        assert second.status_code == 200
        second_body = second.json()
        assert [item["proposal_id"] for item in second_body["items"]] == [
            str(proposal_ids[2])
        ]
        assert second_body["next_cursor"] is None

        detail = reviewer.get(f"/internal/admin/v1/proposals/{proposal_ids[0]}")
        assert detail.status_code == 200
        assert detail.json()["payload"]["secret"] == "payload-101"
    finally:
        get_settings.cache_clear()


def test_queue_filters_invalid_cursor_and_review_state_refresh(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _app(monkeypatch)
    try:
        run_id, proposal_ids = _seed_run(
            app,
            pipeline_code="FILTER_PIPELINE",
            proposal_specs=(
                (201, "QUESTION_DRAFT", "L0"),
                (202, "DECISION_PROBLEM", "L2"),
                (203, "QUESTION_DRAFT", "L2"),
            ),
        )
        _seed_run(
            app,
            pipeline_code="OTHER_PIPELINE",
            proposal_specs=((301, "QUESTION_DRAFT", "L2"),),
        )
        reviewer, csrf = _admin(app, AdminRole.REVIEWER)

        invalid = reviewer.get(
            "/internal/admin/v1/proposals",
            params={"cursor": "not-a-valid-cursor"},
        )
        assert invalid.status_code == 422
        assert invalid.json()["code"] == "ADMIN_PROPOSAL_QUEUE_CURSOR_INVALID"

        filtered = reviewer.get(
            "/internal/admin/v1/proposals",
            params={
                "review_state": "PENDING",
                "proposal_kind": "QUESTION_DRAFT",
                "risk_code": "L2",
                "run_id": str(run_id),
                "pipeline_code": "FILTER_PIPELINE",
            },
        )
        assert filtered.status_code == 200
        assert [item["proposal_id"] for item in filtered.json()["items"]] == [
            str(proposal_ids[2])
        ]

        reviewed = reviewer.post(
            f"/internal/admin/v1/proposals/{proposal_ids[2]}/review",
            headers={ADMIN_CSRF_HEADER: csrf},
            json={
                "decision": "ACCEPTED",
                "policy_version": "proposal-review-v1",
            },
        )
        assert reviewed.status_code == 201

        accepted = reviewer.get(
            "/internal/admin/v1/proposals",
            params={"review_state": "ACCEPTED", "run_id": str(run_id)},
        )
        pending = reviewer.get(
            "/internal/admin/v1/proposals",
            params={"review_state": "PENDING", "run_id": str(run_id)},
        )
        assert [item["proposal_id"] for item in accepted.json()["items"]] == [
            str(proposal_ids[2])
        ]
        assert str(proposal_ids[2]) not in {
            item["proposal_id"] for item in pending.json()["items"]
        }
        detail = reviewer.get(f"/internal/admin/v1/proposals/{proposal_ids[2]}")
        assert detail.json()["review_state"] == "ACCEPTED"
        assert detail.json()["review"]["decision"] == "ACCEPTED"
    finally:
        get_settings.cache_clear()
