from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from hashlib import sha256
from uuid import uuid4

import pytest

from kefe_api.modules.ingestion_orchestration.feed_item_materializer import (
    NORMALIZED_SCHEMA_REF,
    NORMALIZED_SCHEMA_VERSION,
    TARGET_KIND,
    FeedItemProposalMaterializer,
)
from kefe_api.modules.ingestion_orchestration.in_memory import (
    InMemoryIngestionOrchestrationRepository,
)
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
from kefe_api.modules.knowledge.in_memory import InMemoryKnowledgeRepository
from kefe_api.modules.knowledge.models import ArtifactKind, SourceArtifact
from kefe_api.modules.knowledge.source_evidence import (
    canonical_content_hash,
    canonical_storage_ref,
)

SOURCE_BODY = b"<rss>immutable-feed-snapshot</rss>"
SOURCE_HASH = canonical_content_hash(SOURCE_BODY)
SOURCE_REF = canonical_storage_ref(SOURCE_HASH)
ITEM_TITLE = "İnsan onaylı feed maddesi"
ITEM_SUMMARY = "Bu metin yalnız dış kaynak içeriğini normalize eder."
CANONICAL_TEXT = f"{ITEM_TITLE}\n\n{ITEM_SUMMARY}"


class FixedProcessor:
    def __init__(self, draft: ProposalDraft) -> None:
        self._draft = draft

    def process(self, **_) -> StageProcessorResult:
        return StageProcessorResult(proposals=(self._draft,))


def _source() -> SourceArtifact:
    return SourceArtifact.create(
        adapter_code="test.feed_item_source.v1",
        external_locator=f"https://feeds.example.test/{uuid4()}.xml",
        captured_at=datetime(2026, 8, 3, 9, 0, tzinfo=UTC),
        content_hash=SOURCE_HASH,
        publisher_or_issuer="Example Feed",
        language_code="tr",
        jurisdiction_code="TR",
        raw_storage_ref=SOURCE_REF,
    )


def _payload(source: SourceArtifact) -> dict[str, object]:
    return {
        "source_artifact_id": str(source.id),
        "feed_content_hash": source.content_hash,
        "feed_storage_ref": source.raw_storage_ref,
        "feed_format": "RSS_2_0",
        "feed_title": "Example Feed",
        "item_id": "feed-item-42",
        "item_title": ITEM_TITLE,
        "item_url": "https://www.example.test/news/42",
        "published_at": "2026-08-03T08:55:00+00:00",
        "summary_text": ITEM_SUMMARY,
    }


def _proposal_fixture():
    knowledge = InMemoryKnowledgeRepository()
    source = knowledge.add_source_artifact(_source())
    repository = InMemoryIngestionOrchestrationRepository()
    service = IngestionOrchestrationService(repository)
    run = service.start_run(
        input_artifact_kind=InputArtifactKind.SOURCE_ARTIFACT,
        input_artifact_id=source.id,
        input_content_hash=source.content_hash,
        pipeline_code="RSS_ATOM_FEED_ITEM_EXTRACTION",
        pipeline_version="1.0.0",
        configuration_hash="sha256:test-feed-item-materialization",
        locale="tr-TR",
        jurisdiction_code="TR",
    )
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
                payload=_payload(source),
                configuration_version=run.configuration_hash,
                risk_code="UNREVIEWED_EXTERNAL_FEED_ITEM",
                provenance_ref=source.raw_storage_ref,
            )
        ),
    )
    proposal = repository.list_proposals(run.id)[0]
    return knowledge, repository, service, source, proposal


def test_accepted_feed_item_materializes_deterministic_normalized_artifact() -> None:
    knowledge, repository, service, source, proposal = _proposal_fixture()
    review = service.review_proposal(
        proposal_id=proposal.id,
        decision=ProposalReviewDecisionKind.ACCEPTED,
        reviewer_ref="admin:editor:feed-item",
        rationale="Source item is relevant for later editorial work.",
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

    assert first == replay
    assert first.target_kind == TARGET_KIND
    artifact = knowledge.get_normalized_artifact(first.target_id)
    assert artifact is not None
    assert artifact.source_artifact_id == source.id
    assert artifact.artifact_kind is ArtifactKind.EXTERNAL_EVIDENCE
    assert artifact.normalized_at == review.decided_at
    assert artifact.text == CANONICAL_TEXT
    assert artifact.content_hash == (
        f"sha256:{sha256(CANONICAL_TEXT.encode('utf-8')).hexdigest()}"
    )
    assert artifact.language_code == "tr"
    assert artifact.jurisdiction_code == "TR"
    assert artifact.media_metadata == {
        "schema_ref": NORMALIZED_SCHEMA_REF,
        "schema_version": NORMALIZED_SCHEMA_VERSION,
        "feed_format": "RSS_2_0",
        "feed_title": "Example Feed",
        "item_id": "feed-item-42",
        "item_url": "https://www.example.test/news/42",
        "published_at": "2026-08-03T08:55:00+00:00",
        "proposal_id": str(proposal.id),
        "review_id": str(review.id),
        "reviewer_ref": review.reviewer_ref,
        "provenance_ref": f"{source.raw_storage_ref};review:{review.id}",
    }
    assert "feed_storage_ref" not in artifact.media_metadata
    assert repository.find_materialization(
        proposal.id,
        target_kind=TARGET_KIND,
    ) == first


def test_unreviewed_rejected_and_changes_requested_proposals_cannot_materialize() -> None:
    for decision in (
        None,
        ProposalReviewDecisionKind.REJECTED,
        ProposalReviewDecisionKind.CHANGES_REQUESTED,
    ):
        knowledge, _, service, _, proposal = _proposal_fixture()
        if decision is not None:
            service.review_proposal(
                proposal_id=proposal.id,
                decision=decision,
                reviewer_ref="admin:editor:negative",
            )
        with pytest.raises(ValueError, match="ACCEPTED"):
            service.materialize_accepted_proposal(
                proposal_id=proposal.id,
                materializer=FeedItemProposalMaterializer(
                    knowledge_repository=knowledge
                ),
            )


def test_schema_payload_and_source_lineage_drift_fail_closed() -> None:
    knowledge, repository, service, source, proposal = _proposal_fixture()
    review = service.review_proposal(
        proposal_id=proposal.id,
        decision=ProposalReviewDecisionKind.ACCEPTED,
        reviewer_ref="admin:editor:drift",
    )
    materializer = FeedItemProposalMaterializer(
        knowledge_repository=knowledge
    )

    with pytest.raises(ValueError, match="schema version"):
        materializer.materialize(
            proposal=replace(proposal, payload_schema_version="2.0.0"),
            review=review,
        )
    with pytest.raises(ValueError, match="payload fields"):
        materializer.materialize(
            proposal=replace(
                proposal,
                payload={key: value for key, value in proposal.payload.items() if key != "item_id"},
            ),
            review=review,
        )
    with pytest.raises(ValueError, match="content hash"):
        materializer.materialize(
            proposal=replace(
                proposal,
                payload={**proposal.payload, "feed_content_hash": canonical_content_hash(b"wrong")},
            ),
            review=review,
        )
    with pytest.raises(ValueError, match="storage reference"):
        materializer.materialize(
            proposal=replace(
                proposal,
                payload={
                    **proposal.payload,
                    "feed_storage_ref": canonical_storage_ref(
                        canonical_content_hash(b"wrong")
                    ),
                },
            ),
            review=review,
        )

    with pytest.raises(ValueError, match="not materializable"):
        KnowledgeProposalMaterializer(
            knowledge_repository=knowledge,
            orchestration_repository=repository,
        ).materialize(proposal=proposal, review=review)
    assert knowledge.get_source_artifact(source.id) == source


def test_noncanonical_item_fields_and_conflicting_target_fail_closed() -> None:
    knowledge, _, service, source, proposal = _proposal_fixture()
    review = service.review_proposal(
        proposal_id=proposal.id,
        decision=ProposalReviewDecisionKind.ACCEPTED,
        reviewer_ref="admin:editor:canonical",
    )
    materializer = FeedItemProposalMaterializer(
        knowledge_repository=knowledge
    )

    with pytest.raises(ValueError, match="item_title"):
        materializer.materialize(
            proposal=replace(
                proposal,
                payload={**proposal.payload, "item_title": " padded title "},
            ),
            review=review,
        )
    with pytest.raises(ValueError, match="item_url"):
        materializer.materialize(
            proposal=replace(
                proposal,
                payload={**proposal.payload, "item_url": "https://user@example.test/x"},
            ),
            review=review,
        )
    assert knowledge.get_source_artifact(source.id) == source
