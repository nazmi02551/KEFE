from __future__ import annotations

import os
from datetime import UTC, datetime
from uuid import NAMESPACE_URL, uuid4, uuid5

import pytest
from sqlalchemy import create_engine, text

from kefe_api.infrastructure.postgres_ingestion_orchestration import (
    PostgresIngestionOrchestrationRepository,
)
from kefe_api.infrastructure.postgres_knowledge import PostgresKnowledgeRepository
from kefe_api.modules.ingestion_orchestration.knowledge_materializer import (
    KnowledgeProposalMaterializer,
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
from kefe_api.modules.knowledge.models import (
    ArtifactKind,
    NormalizedArtifact,
    SourceArtifact,
)
from kefe_api.modules.knowledge.source_evidence import (
    canonical_content_hash,
    canonical_storage_ref,
)

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)


class FeedItemProcessor:
    def __init__(self, source: SourceArtifact, *, item_id: str) -> None:
        self._source = source
        self._item_id = item_id

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
                        "feed_format": "ATOM_1_0",
                        "feed_title": "PostgreSQL Feed",
                        "item_id": self._item_id,
                        "item_title": "PostgreSQL reviewed item",
                        "item_url": "https://news.example.test/postgres/item",
                        "published_at": "2026-08-03T05:00:00+00:00",
                        "summary_text": "Persisted reviewed summary.",
                    },
                    configuration_version="feed-item-extraction-v1",
                    risk_code="UNREVIEWED_EXTERNAL_FEED_ITEM",
                    provenance_ref=source.raw_storage_ref,
                ),
            ),
            output_metadata={"fixture": "postgres-feed-item"},
        )


def _create_proposal(
    *,
    service: IngestionOrchestrationService,
    orchestration: PostgresIngestionOrchestrationRepository,
    source: SourceArtifact,
    item_id: str,
):
    run = service.start_run(
        input_artifact_kind=InputArtifactKind.SOURCE_ARTIFACT,
        input_artifact_id=source.id,
        input_content_hash=source.content_hash,
        pipeline_code=f"RSS_ATOM_FEED_ITEM_EXTRACTION_{uuid4()}",
        pipeline_version="1.0.0",
        configuration_hash=f"sha256:postgres-feed-item-{uuid4()}",
        locale="en-GB",
        jurisdiction_code="GB",
    )
    service.execute_stage(
        run_id=run.id,
        stage_code="EXTRACT_FEED_ITEMS",
        stage_version="1.0.0",
        input_hash=source.content_hash,
        max_attempts=1,
        executor_kind=ExecutorKind.DETERMINISTIC,
        processor=FeedItemProcessor(source, item_id=item_id),
    )
    proposal = orchestration.list_proposals(run.id)[0]
    review = service.review_proposal(
        proposal_id=proposal.id,
        decision=ProposalReviewDecisionKind.ACCEPTED,
        reviewer_ref="admin:postgres-feed-editor",
        rationale="PostgreSQL fixture reviewed.",
        reason_code="EDITORIAL_SOURCE_CHECKED",
        policy_version="feed-review-v1",
    )
    return proposal, review


def test_postgres_feed_item_partial_retry_and_conflict_are_deterministic() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    knowledge = PostgresKnowledgeRepository(engine)
    orchestration = PostgresIngestionOrchestrationRepository(engine)
    service = IngestionOrchestrationService(orchestration)
    content_hash = canonical_content_hash(f"postgres-feed-{uuid4()}".encode())
    source = knowledge.add_source_artifact(
        SourceArtifact.create(
            adapter_code="test.postgres.rss.v1",
            external_locator=f"https://feeds.example.test/{uuid4()}.xml",
            captured_at=datetime(2026, 8, 3, 5, 5, tzinfo=UTC),
            content_hash=content_hash,
            publisher_or_issuer="PostgreSQL Feed",
            language_code="en",
            jurisdiction_code="GB",
            raw_storage_ref=canonical_storage_ref(content_hash),
        )
    )
    proposal, review = _create_proposal(
        service=service,
        orchestration=orchestration,
        source=source,
        item_id=f"urn:postgres:item:{uuid4()}",
    )
    materializer = KnowledgeProposalMaterializer(
        knowledge_repository=knowledge,
        orchestration_repository=orchestration,
    )

    target_kind, target_id = materializer.materialize(
        proposal=proposal,
        review=review,
    )
    assert target_kind == "NORMALIZED_ARTIFACT"
    assert orchestration.find_materialization(proposal.id) is None

    first = service.materialize_accepted_proposal(
        proposal_id=proposal.id,
        materializer=materializer,
    )
    replay = service.materialize_accepted_proposal(
        proposal_id=proposal.id,
        materializer=materializer,
    )
    assert replay == first
    assert first.target_id == target_id

    artifact = knowledge.get_normalized_artifact(target_id)
    assert artifact is not None
    assert artifact.artifact_kind is ArtifactKind.EXTERNAL_EVIDENCE
    assert artifact.normalized_at == review.decided_at
    assert artifact.media_metadata["review_id"] == str(review.id)
    assert artifact.media_metadata["feed_storage_ref"] == source.raw_storage_ref

    with engine.connect() as connection:
        normalized_count = connection.execute(
            text(
                """
                SELECT count(*) FROM knowledge.normalized_artifact
                WHERE id = :target_id
                """
            ),
            {"target_id": target_id},
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

    conflict_proposal, _ = _create_proposal(
        service=service,
        orchestration=orchestration,
        source=source,
        item_id=f"urn:postgres:conflict:{uuid4()}",
    )
    conflict_id = uuid5(
        NAMESPACE_URL,
        f"kefe:proposal:{conflict_proposal.id}:NORMALIZED_ARTIFACT",
    )
    knowledge.add_normalized_artifact(
        NormalizedArtifact(
            id=conflict_id,
            source_artifact_id=source.id,
            artifact_kind=ArtifactKind.EXTERNAL_EVIDENCE,
            normalized_at=datetime(2026, 8, 3, 5, 30, tzinfo=UTC),
            content_hash="sha256:postgres-conflict",
            text="Conflicting PostgreSQL artifact",
            language_code="en",
            jurisdiction_code="GB",
            media_metadata={"conflict": True},
        )
    )

    with pytest.raises(ValueError, match="conflicting normalized artifact"):
        service.materialize_accepted_proposal(
            proposal_id=conflict_proposal.id,
            materializer=materializer,
        )
