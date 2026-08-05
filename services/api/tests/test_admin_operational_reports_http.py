from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from kefe_api.main import create_app
from kefe_api.modules.admin_security.in_memory import InMemoryAdminSessionStore
from kefe_api.modules.admin_security.models import AdminRole
from kefe_api.modules.admin_security.router import ADMIN_SESSION_COOKIE
from kefe_api.modules.community_reason.models import (
    CommunityReason,
    CommunityReasonModeration,
    ReasonReportCode,
)
from kefe_api.modules.content_authoring.models import (
    AuthoringCaseVersion,
    CaseIdentity,
    ContentLifecycle,
    LifecycleAuditEntry,
)
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

ENDPOINT = "/internal/admin/v1/operational-reports/snapshot"


def _issue_admin(app, role: AdminRole) -> TestClient:
    store = app.state.admin_session_store
    assert isinstance(store, InMemoryAdminSessionStore)
    subject_id = uuid4()
    store.upsert_subject(subject_id, roles=frozenset({role}))
    now = datetime.now(UTC)
    issued = store.issue(
        admin_subject_id=subject_id,
        authenticated_at=now,
        mfa_satisfied_at=now,
        expires_at=now + timedelta(hours=12),
    )
    client = TestClient(app)
    client.cookies.set(ADMIN_SESSION_COOKIE, issued.session_token)
    return client


def _seed_case_state(app, state: ContentLifecycle) -> None:
    case_id = uuid4()
    version = AuthoringCaseVersion(
        id=uuid4(),
        case_id=case_id,
        version_no=1,
        state=state,
        title="Operational aggregate fixture",
        summary="Aggregate-only lifecycle count fixture.",
        base_format_code="DILEMMA",
        primary_domain_code="DAILY_LIFE",
        content_risk="L0",
        issues=(),
    )
    app.state.content_authoring_repository.create_case(
        identity=CaseIdentity(id=case_id, slug=f"report-{state.value.lower()}-{case_id.hex}"),
        initial_version=version,
        audit=LifecycleAuditEntry.create(
            version=version,
            actor_ref="test:operational-report",
            command="seed",
            previous_state=None,
            new_state=state,
        ),
    )


def _seed_proposal(app, decision: ProposalReviewDecisionKind | None) -> None:
    repository = app.state.ingestion_orchestration_repository
    now = datetime.now(UTC)
    run_id = uuid4()
    artifact_id = uuid4()
    stage_id = uuid4()
    proposal_id = uuid4()
    run = IngestionRun(
        id=run_id,
        run_key=f"operational-report-{run_id}",
        input_artifact_kind=InputArtifactKind.SOURCE_ARTIFACT,
        input_artifact_id=artifact_id,
        input_content_hash="a" * 64,
        pipeline_code="OPERATIONAL_REPORT_TEST",
        pipeline_version="1",
        configuration_hash="b" * 64,
        state=IngestionRunState.RUNNING,
        created_at=now,
        updated_at=now,
    )
    repository.create_or_get_run(run)
    stage = StageExecution(
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
    repository.add_stage_execution(stage)
    payload = {"fixture": decision.value if decision is not None else "PENDING"}
    proposal = Proposal(
        id=proposal_id,
        proposal_kind="CASE_CANDIDATE",
        payload_schema_ref="urn:kefe:test:operational-report",
        payload_schema_version="1",
        payload=payload,
        payload_hash=stable_payload_hash(payload),
        run_id=run_id,
        stage_execution_id=stage_id,
        created_at=now,
        risk_code="L0",
    )
    repository.add_proposal(proposal)
    if decision is not None:
        repository.add_review_decision(
            ProposalReviewDecision(
                id=uuid4(),
                proposal_id=proposal_id,
                decision=decision,
                reviewer_ref="test:reviewer",
                decided_at=now,
            )
        )


def _seed_reason(app, state: CommunityReasonModeration, *, reported: bool) -> UUID:
    now = datetime.now(UTC)
    reason = CommunityReason(
        id=uuid4(),
        actor_id=uuid4(),
        session_id=uuid4(),
        case_version_id=uuid4(),
        tags=("FAIRNESS",),
        body="Aggregate fixture" if state is CommunityReasonModeration.PENDING else None,
        moderation_state=state,
        created_at=now,
        updated_at=now,
    )
    app.state.community_reason_repository.create_or_replace(reason)
    if reported:
        app.state.community_reason_repository.report(
            report_id=uuid4(),
            reason_id=reason.id,
            reporter_actor_id=uuid4(),
            report_code=ReasonReportCode.PERSONAL_DATA,
            created_at=now + timedelta(seconds=1),
        )
    return reason.id


def test_snapshot_requires_dedicated_capability_and_no_csrf_or_step_up() -> None:
    app = create_app()
    editor = _issue_admin(app, AdminRole.EDITOR)
    denied = editor.get(ENDPOINT)
    assert denied.status_code == 403
    assert denied.json()["code"] == "ADMIN_FORBIDDEN"
    assert denied.json()["meta"]["required_capability"] == ("OPERATIONAL_REPORT_READ")

    for role in (AdminRole.REVIEWER, AdminRole.PUBLISHER, AdminRole.ACCESS_ADMIN):
        client = _issue_admin(app, role)
        response = client.get(ENDPOINT)
        assert response.status_code == 200

    assert editor.post(ENDPOINT).status_code == 405
    assert editor.put(ENDPOINT).status_code == 405
    assert editor.delete(ENDPOINT).status_code == 405


def test_snapshot_uses_authoritative_aggregate_counts_and_is_privacy_safe() -> None:
    app = create_app()
    for state in ContentLifecycle:
        _seed_case_state(app, state)
    _seed_proposal(app, None)
    _seed_proposal(app, ProposalReviewDecisionKind.ACCEPTED)
    _seed_proposal(app, ProposalReviewDecisionKind.REJECTED)
    _seed_proposal(app, ProposalReviewDecisionKind.CHANGES_REQUESTED)
    _seed_reason(app, CommunityReasonModeration.PENDING, reported=False)
    _seed_reason(app, CommunityReasonModeration.NOT_REQUIRED, reported=True)
    _seed_reason(app, CommunityReasonModeration.BLOCKED, reported=True)

    reviewer = _issue_admin(app, AdminRole.REVIEWER)
    before_audit = list(app.state.community_reason_repository._audits)
    response = reviewer.get(ENDPOINT)
    assert response.status_code == 200
    body = response.json()
    assert body["aggregate_only"] is True
    assert set(body["editorial_lifecycle"]) == {state.value for state in ContentLifecycle}
    assert set(body["editorial_lifecycle"].values()) == {1}
    assert body["proposal_review"] == {
        "PENDING": 1,
        "ACCEPTED": 1,
        "REJECTED": 1,
        "CHANGES_REQUESTED": 1,
    }
    assert body["moderation"] == {"PENDING": 1, "REPORTED": 1}
    assert body["as_of"] == body["content_supply"]["as_of"]
    assert body["thresholds"] == {
        "in_review_attention_threshold": 50,
        "pending_proposal_attention_threshold": 100,
        "moderation_candidate_attention_threshold": 50,
    }
    assert list(app.state.community_reason_repository._audits) == before_audit

    rendered = str(body).lower()
    for forbidden in (
        "case_id",
        "case_version_id",
        "proposal_id",
        "reason_id",
        "actor_id",
        "reporter_actor_id",
        "session_id",
        "reason_body",
        "rationale",
        "source_locator",
        "credential",
        "secret",
        "backend_object_key",
    ):
        assert forbidden not in rendered


def test_signal_is_transparent_and_threshold_driven() -> None:
    app = create_app()
    service = app.state.admin_operational_reports_service
    policy = service.snapshot().policy
    for _ in range(policy.moderation_candidate_attention_threshold + 1):
        _seed_reason(app, CommunityReasonModeration.PENDING, reported=False)
    snapshot = service.snapshot(policy)
    assert snapshot.overall_signal.value == "ATTENTION"
    assert snapshot.reason_codes == ("MODERATION_BACKLOG",)
