from __future__ import annotations

import os
from datetime import UTC, datetime
from hashlib import sha256
from uuid import uuid4

import pytest
from sqlalchemy import create_engine

from kefe_api.infrastructure.postgres_ingestion_orchestration import (
    PostgresIngestionOrchestrationRepository,
)
from kefe_api.infrastructure.postgres_knowledge import PostgresKnowledgeRepository
from kefe_api.modules.ingestion_orchestration.feed_item_materializer import (
    FeedItemProposalMaterializer,
    TARGET_KIND,
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
from kefe_api.modules.knowledge.models import ArtifactKind, SourceArtifact
from kefe_api.modules.knowledge.source_evidence import (
    canonical_content_hash,
    canonical_storage_ref,
)

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)


class FixedProcessor:
    def __init__(self, draft: ProposalDraft) -> None:
        self._draft = draft

    def process(self, **_) -> StageProcessorResult:
        return StageProcessorResult(proposals=(self._draft,))


def test_postgres_accepted_feed_item_materialization_is_idempotent() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    knowledge = PostgresKnowledgeRepository(engine)
    repository = PostgresIngestionOrchestrationRepository(engine)
    service = IngestionOrchestrationService(repository)

    source_hash = canonical_content_hash(f"feed:{uuid4()}".encode())
    source = knowledge.add_source_artifact(
        SourceArtifact.create(
            adapter_code="test.pg_feed_item.v1",
            external_locator=f"https://feeds.example.test/{uuid4()}.xml",
            captured_at=datetime(2026, 8, 3, 9, 30, tzinfo=UTC),
            content_hash=source_hash,
            publisher_or_issuer="PostgreSQL Feed",
            language_code="en",
            jurisdiction_code="ZZ",
            raw_storage_ref=canonical_storage_ref(source_hash),
        )
    )
    run = service.start_run(
        input_artifact_kind=InputArtifactKind.SOURCE_ARTIFACT,
        input_artifact_id=source.id,
        input_content_hash=source.content_hash,
        pipeline_code="RSS_ATOM_FEED_ITEM_EXTRACTION",
        pipeline_version="1.0.0",
        configuration_hash=f"sha256:{uuid4().hex}",
        locale="en",
        jurisdiction_code="ZZ",
    )
    title = "PostgreSQL materialized feed item"
    summary = "Human review gates this normalized external evidence."
    service.execute_stage(
        run_id=run.id,
        stage_code="EXTRACT_FEED_ITEMS",
        stage_version="1.0.0",
        input_hash=source.content_hash,
        max_attempts=1,
        executor_kind=ExecutorKind.DETERMINISTIC,
        processor=FixedProcessor(
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
                    "item_id": f"urn:uuid:{uuid4()}",
                    "item_title": title,
                    "item_url": "https://www.example.test/postgres/item",
                    "published_at": "2026-08-03T09:25:00+00:00",
                    "summary_text": summary,
                },
                risk_code="UNREVIEWED_EXTERNAL_FEED_ITEM",
                provenance_ref=source.raw_storage_ref,
            )
        ),
    )
    proposal = repository.list_proposals(run.id)[0]
    review = service.review_proposal(
        proposal_id=proposal.id,
        decision=ProposalReviewDecisionKind.ACCEPTED,
        reviewer_ref="admin:postgres:feed-item",
    )
    materializer = FeedItemProposalMaterializer(
        knowledge_repository=knowledge
    )

    first = service.materialize_accepted_proposal(
        proposal_id=proposal.id,
        materializer=materializer,
    )
    replay = service.materialize_accepted_proposal(
        proposal_id=proposal.id,
        materializer=materializer,
    )

    assert replay == first
    assert first.target_kind == TARGET_KIND
    artifact = knowledge.get_normalized_artifact(first.target_id)
    assert artifact is not None
    assert artifact.artifact_kind is ArtifactKind.EXTERNAL_EVIDENCE
    assert artifact.source_artifact_id == source.id
    assert artifact.normalized_at == review.decided_at
    assert artifact.text == f"{title}\n\n{summary}"
    assert artifact.content_hash == (
        f"sha256:{sha256(artifact.text.encode('utf-8')).hexdigest()}"
    )
    assert artifact.language_code == "en"
    assert artifact.jurisdiction_code == "ZZ"
    assert repository.find_materialization(
        proposal.id,
        target_kind=TARGET_KIND,
    ) == first
