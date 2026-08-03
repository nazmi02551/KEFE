from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import create_engine

from kefe_api.core.errors import DomainError
from kefe_api.infrastructure.postgres_ingestion_orchestration import (
    PostgresIngestionOrchestrationRepository,
)
from kefe_api.modules.admin_security.feed_item_materialization_status import (
    FeedItemMaterializationStatus,
    SecuredFeedItemMaterializationStatusService,
)
from kefe_api.modules.admin_security.models import (
    AdminCapability,
    AdminPrincipal,
    AdminRole,
)
from kefe_api.modules.ingestion_orchestration.models import (
    ExecutorKind,
    InputArtifactKind,
    ProposalDraft,
    ProposalMaterialization,
    ProposalReviewDecisionKind,
    StageProcessorResult,
)
from kefe_api.modules.ingestion_orchestration.service import (
    IngestionOrchestrationService,
)

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)


class RecordingSecurity:
    def __init__(self) -> None:
        self.capabilities: list[AdminCapability] = []

    def authorize(self, principal, capability, *, now=None) -> None:
        del principal, now
        self.capabilities.append(capability)


class FixedProcessor:
    def process(self, **_) -> StageProcessorResult:
        return StageProcessorResult(
            proposals=(
                ProposalDraft(
                    proposal_kind="FEED_ITEM",
                    payload_schema_ref="kefe.feed-item",
                    payload_schema_version="1.0.0",
                    payload={"fixture": "status-read-does-not-validate-payload"},
                    risk_code="UNREVIEWED_EXTERNAL_FEED_ITEM",
                    provenance_ref="evidence://sha256/" + "0" * 64,
                ),
            )
        )


def _principal() -> AdminPrincipal:
    now = datetime.now(UTC)
    return AdminPrincipal(
        admin_subject_id=uuid4(),
        session_id=uuid4(),
        roles=frozenset({AdminRole.REVIEWER}),
        direct_capabilities=frozenset(),
        authenticated_at=now,
        mfa_satisfied_at=now,
        step_up_at=None,
        expires_at=now + timedelta(hours=1),
        last_seen_at=now,
    )


def _proposal(service, repository):
    run = service.start_run(
        input_artifact_kind=InputArtifactKind.SOURCE_ARTIFACT,
        input_artifact_id=uuid4(),
        input_content_hash=f"sha256:{uuid4()}",
        pipeline_code=f"STATUS_POSTGRES_{uuid4()}",
        pipeline_version="1.0.0",
        configuration_hash=f"sha256:status-postgres-{uuid4()}",
    )
    service.execute_stage(
        run_id=run.id,
        stage_code="PROPOSE",
        stage_version="1.0.0",
        input_hash=run.input_content_hash,
        max_attempts=1,
        executor_kind=ExecutorKind.DETERMINISTIC,
        processor=FixedProcessor(),
    )
    return repository.list_proposals(run.id)[0]


def test_postgres_status_progression_and_conflict_are_persisted() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    repository = PostgresIngestionOrchestrationRepository(engine)
    orchestration = IngestionOrchestrationService(repository)
    security = RecordingSecurity()
    status = SecuredFeedItemMaterializationStatusService(
        repository=repository,
        security=security,  # type: ignore[arg-type]
    )
    principal = _principal()
    proposal = _proposal(orchestration, repository)

    initial = status.observe(principal, proposal_id=proposal.id)
    assert initial.status is FeedItemMaterializationStatus.REVIEW_REQUIRED

    review = orchestration.review_proposal(
        proposal_id=proposal.id,
        decision=ProposalReviewDecisionKind.ACCEPTED,
        reviewer_ref="admin:postgres-status",
    )
    ready = status.observe(principal, proposal_id=proposal.id)
    assert ready.status is FeedItemMaterializationStatus.READY
    assert ready.proposal_review_decision_id == review.id

    materialization = ProposalMaterialization(
        id=uuid4(),
        proposal_id=proposal.id,
        review_decision_id=review.id,
        target_kind="NORMALIZED_ARTIFACT",
        target_id=uuid4(),
        materialized_at=datetime.now(UTC),
    )
    repository.add_materialization(materialization)
    completed = status.observe(principal, proposal_id=proposal.id)
    assert completed.status is FeedItemMaterializationStatus.MATERIALIZED
    assert completed.proposal_materialization_id == materialization.id
    assert completed.target_id == materialization.target_id
    assert security.capabilities == [
        AdminCapability.CONTENT_REVIEW,
        AdminCapability.SOURCE_VERIFY,
    ] * 3

    conflict_proposal = _proposal(orchestration, repository)
    conflict_review = orchestration.review_proposal(
        proposal_id=conflict_proposal.id,
        decision=ProposalReviewDecisionKind.ACCEPTED,
        reviewer_ref="admin:postgres-status",
    )
    repository.add_materialization(
        ProposalMaterialization(
            id=uuid4(),
            proposal_id=conflict_proposal.id,
            review_decision_id=conflict_review.id,
            target_kind="CLAIM",
            target_id=uuid4(),
            materialized_at=datetime.now(UTC),
        )
    )
    with pytest.raises(DomainError) as conflict:
        status.observe(principal, proposal_id=conflict_proposal.id)
    assert conflict.value.code == "INGESTION_FEED_ITEM_MATERIALIZATION_STATUS_CONFLICT"
