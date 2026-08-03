from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine, text

from kefe_api.core.errors import DomainError
from kefe_api.infrastructure.postgres_ingestion_orchestration import (
    PostgresIngestionOrchestrationRepository,
)
from kefe_api.infrastructure.postgres_knowledge import PostgresKnowledgeRepository
from kefe_api.modules.admin_security.feed_item_materialization import (
    SecuredFeedItemMaterializationService,
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
    ProposalReviewDecisionKind,
    StageProcessorResult,
)
from kefe_api.modules.ingestion_orchestration.service import (
    IngestionOrchestrationService,
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


class RecordingSecurity:
    def __init__(self) -> None:
        self.capabilities: list[AdminCapability] = []

    def authorize(
        self,
        principal: AdminPrincipal,
        capability: AdminCapability,
        *,
        now=None,
    ) -> None:
        del principal, now
        self.capabilities.append(capability)


class FeedItemProcessor:
    def __init__(self, source: SourceArtifact) -> None:
        self._source = source

    def process(self, **_) -> StageProcessorResult:
        source = self._source
        return StageProcessorResult(
            proposals=(
                ProposalDraft(
                    proposal_kind="FEED_ITEM",
                    payload_schema_ref="kefe.feed-item",
                    payload_schema_version="1.0.0",
                    payload={
                        "source_artifact_id": str(source.id),
                        "feed_content_hash": source.content_hash,
                        "feed_storage_ref": source.raw_storage_ref,
                        "feed_format": "RSS_2_0",
                        "feed_title": "Secured PostgreSQL Feed",
                        "item_id": f"urn:secured-postgres:{uuid4()}",
                        "item_title": "Secured PostgreSQL item",
                        "item_url": "https://news.example.test/secured-postgres",
                        "published_at": "2026-08-03T05:40:00+00:00",
                        "summary_text": "Secured PostgreSQL summary.",
                    },
                    configuration_version="admin-feed-item-v1",
                    risk_code="UNREVIEWED_EXTERNAL_FEED_ITEM",
                    provenance_ref=source.raw_storage_ref,
                ),
            ),
            output_metadata={"fixture": "secured-postgres"},
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


def test_secured_postgres_command_authorizes_and_replays_one_materialization() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    knowledge = PostgresKnowledgeRepository(engine)
    repository = PostgresIngestionOrchestrationRepository(engine)
    orchestration = IngestionOrchestrationService(repository)
    content_hash = canonical_content_hash(f"secured-postgres-{uuid4()}".encode())
    source = knowledge.add_source_artifact(
        SourceArtifact.create(
            adapter_code="test.secured.postgres.rss.v1",
            external_locator=f"https://feeds.example.test/{uuid4()}.xml",
            captured_at=datetime(2026, 8, 3, 5, 45, tzinfo=UTC),
            content_hash=content_hash,
            publisher_or_issuer="Secured PostgreSQL Feed",
            language_code="en",
            jurisdiction_code="GB",
            raw_storage_ref=canonical_storage_ref(content_hash),
        )
    )
    run = orchestration.start_run(
        input_artifact_kind=InputArtifactKind.SOURCE_ARTIFACT,
        input_artifact_id=source.id,
        input_content_hash=source.content_hash,
        pipeline_code=f"SECURED_ADMIN_FEED_{uuid4()}",
        pipeline_version="1.0.0",
        configuration_hash=f"sha256:secured-admin-feed-{uuid4()}",
        locale="en-GB",
        jurisdiction_code="GB",
    )
    orchestration.execute_stage(
        run_id=run.id,
        stage_code="PROPOSE",
        stage_version="1.0.0",
        input_hash=source.content_hash,
        max_attempts=1,
        executor_kind=ExecutorKind.DETERMINISTIC,
        processor=FeedItemProcessor(source),
    )
    proposal = repository.list_proposals(run.id)[0]
    review = orchestration.review_proposal(
        proposal_id=proposal.id,
        decision=ProposalReviewDecisionKind.ACCEPTED,
        reviewer_ref="admin:postgres-feed-reviewer",
        policy_version="proposal-review-v1",
    )
    security = RecordingSecurity()
    secured = SecuredFeedItemMaterializationService(
        orchestration=orchestration,
        repository=repository,
        knowledge=knowledge,
        security=security,  # type: ignore[arg-type]
    )
    principal = _principal()

    first = secured.materialize(
        principal,
        proposal_id=proposal.id,
        proposal_review_decision_id=review.id,
    )
    replay = secured.materialize(
        principal,
        proposal_id=proposal.id,
        proposal_review_decision_id=review.id,
    )

    assert replay == first
    assert first.target_kind == "NORMALIZED_ARTIFACT"
    assert security.capabilities == [
        AdminCapability.CONTENT_REVIEW,
        AdminCapability.SOURCE_VERIFY,
        AdminCapability.CONTENT_REVIEW,
        AdminCapability.SOURCE_VERIFY,
    ]
    artifact = knowledge.get_normalized_artifact(first.target_id)
    assert artifact is not None
    assert artifact.source_artifact_id == source.id

    with engine.connect() as connection:
        normalized_count = connection.execute(
            text(
                "SELECT count(*) FROM knowledge.normalized_artifact WHERE id = :id"
            ),
            {"id": first.target_id},
        ).scalar_one()
        materialization_count = connection.execute(
            text(
                """
                SELECT count(*) FROM ingestion.proposal_materialization
                WHERE proposal_id = :proposal_id
                  AND target_kind = 'NORMALIZED_ARTIFACT'
                """
            ),
            {"proposal_id": proposal.id},
        ).scalar_one()
    assert normalized_count == 1
    assert materialization_count == 1

    with pytest.raises(DomainError) as mismatch:
        secured.materialize(
            principal,
            proposal_id=proposal.id,
            proposal_review_decision_id=uuid4(),
        )
    assert mismatch.value.code == "INGESTION_PROPOSAL_REVIEW_BINDING_MISMATCH"


def test_secured_postgres_command_reports_not_found_without_materialization() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    knowledge = PostgresKnowledgeRepository(engine)
    repository = PostgresIngestionOrchestrationRepository(engine)
    secured = SecuredFeedItemMaterializationService(
        orchestration=IngestionOrchestrationService(repository),
        repository=repository,
        knowledge=knowledge,
        security=RecordingSecurity(),  # type: ignore[arg-type]
    )

    with pytest.raises(DomainError) as missing:
        secured.materialize(
            _principal(),
            proposal_id=uuid4(),
            proposal_review_decision_id=uuid4(),
        )
    assert missing.value.code == "INGESTION_PROPOSAL_NOT_FOUND"
    assert missing.value.status_code == 404
