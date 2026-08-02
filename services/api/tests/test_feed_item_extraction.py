from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from kefe_api.modules.ingestion_orchestration.feed_item_extraction import (
    PAYLOAD_SCHEMA_REF,
    PAYLOAD_SCHEMA_VERSION,
    PIPELINE_CODE,
    PIPELINE_VERSION,
    PROPOSAL_KIND,
    STAGE_CODE,
    STAGE_VERSION,
    FeedItemExtractionStageProcessor,
    build_feed_item_extraction_runtime,
)
from kefe_api.modules.ingestion_orchestration.in_memory import (
    InMemoryIngestionOrchestrationRepository,
)
from kefe_api.modules.ingestion_orchestration.in_memory_leases import (
    InMemoryIngestionRunLeaseRepository,
)
from kefe_api.modules.ingestion_orchestration.lease_service import (
    IngestionRunLeaseService,
)
from kefe_api.modules.ingestion_orchestration.models import (
    IngestionRun,
    IngestionRunState,
    InputArtifactKind,
)
from kefe_api.modules.ingestion_orchestration.service import (
    FinalStageError,
    IngestionOrchestrationService,
    RetryableStageError,
)
from kefe_api.modules.ingestion_orchestration.worker_runtime import (
    IngestionWorkerRunOutcome,
    InMemoryIngestionWorkerObserver,
)
from kefe_api.modules.ingestion_orchestration.worker_service import (
    IngestionWorkerRunner,
)
from kefe_api.modules.knowledge.in_memory import InMemoryKnowledgeRepository
from kefe_api.modules.knowledge.models import SourceArtifact
from kefe_api.modules.knowledge.rss_atom_capture import StrictRssAtomParseProfile
from kefe_api.modules.knowledge.source_evidence import (
    InMemoryRawSourceEvidenceStore,
    RetryableRawSourceEvidenceError,
    canonical_content_hash,
    canonical_storage_ref,
)

NOW = datetime(2026, 8, 3, 2, 30, tzinfo=UTC)
ADAPTER_CODE = "test.feed_items.v1"
FEED_URL = "https://feeds.example.test/news.xml"

RSS_BODY = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Example News</title>
    <link>https://www.example.test/news</link>
    <description>Example feed</description>
    <lastBuildDate>Sun, 03 Aug 2026 01:00:00 GMT</lastBuildDate>
    <item>
      <guid>z-item</guid>
      <title>Second in deterministic order</title>
      <link>https://www.example.test/news/z</link>
      <pubDate>Sun, 03 Aug 2026 00:50:00 GMT</pubDate>
      <description>Bounded second summary.</description>
    </item>
    <item>
      <guid>a-item</guid>
      <title>First in deterministic order</title>
      <link>https://www.example.test/news/a</link>
      <pubDate>Sun, 03 Aug 2026 00:40:00 GMT</pubDate>
      <description>Bounded first summary.</description>
    </item>
  </channel>
</rss>
"""

ATOM_BODY = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <id>urn:example:feed</id>
  <title>Atom Feed</title>
  <updated>2026-08-03T01:10:00Z</updated>
  <entry>
    <id>urn:item:2</id>
    <title>Atom second</title>
    <updated>2026-08-03T01:02:00Z</updated>
    <link rel="alternate" href="https://www.example.test/atom/2" />
    <summary>Second atom summary.</summary>
  </entry>
  <entry>
    <id>urn:item:1</id>
    <title>Atom first</title>
    <updated>2026-08-03T01:01:00+00:00</updated>
    <content>First atom content.</content>
  </entry>
</feed>
"""


class RetryableReader:
    def read(self, **kwargs):
        del kwargs
        raise RetryableRawSourceEvidenceError("RAW_EVIDENCE_BACKEND_UNAVAILABLE")


def _seed(
    body: bytes,
    *,
    media_type: str,
) -> tuple[
    InMemoryKnowledgeRepository,
    InMemoryRawSourceEvidenceStore,
    SourceArtifact,
]:
    knowledge = InMemoryKnowledgeRepository()
    evidence = InMemoryRawSourceEvidenceStore()
    seal = evidence.seal(
        adapter_code=ADAPTER_CODE,
        body=body,
        media_type=media_type,
        sealed_at=NOW,
    )
    artifact = SourceArtifact.create(
        adapter_code=ADAPTER_CODE,
        external_locator=FEED_URL,
        captured_at=NOW,
        content_hash=seal.content_hash,
        external_id=FEED_URL,
        canonical_url=FEED_URL,
        publisher_or_issuer="fixture",
        raw_storage_ref=seal.storage_ref,
    )
    knowledge.add_source_artifact(artifact)
    return knowledge, evidence, artifact


def _run(artifact: SourceArtifact) -> IngestionRun:
    return IngestionRun(
        id=uuid4(),
        run_key="feed-item-run-key",
        input_artifact_kind=InputArtifactKind.SOURCE_ARTIFACT,
        input_artifact_id=artifact.id,
        input_content_hash=artifact.content_hash,
        pipeline_code=PIPELINE_CODE,
        pipeline_version=PIPELINE_VERSION,
        configuration_hash="sha256:feed-item-config",
        state=IngestionRunState.RUNNING,
        created_at=NOW,
        updated_at=NOW,
    )


def test_rss_stage_emits_deterministic_reviewable_proposals() -> None:
    knowledge, evidence, artifact = _seed(
        RSS_BODY,
        media_type="application/rss+xml",
    )
    processor = FeedItemExtractionStageProcessor(
        knowledge=knowledge,
        evidence=evidence,
    )

    first = processor.process(
        run=_run(artifact),
        stage_code=STAGE_CODE,
        stage_version=STAGE_VERSION,
        input_hash=artifact.content_hash,
    )
    second = processor.process(
        run=_run(artifact),
        stage_code=STAGE_CODE,
        stage_version=STAGE_VERSION,
        input_hash=artifact.content_hash,
    )

    assert first.output_hash == second.output_hash
    assert [proposal.payload["item_id"] for proposal in first.proposals] == [
        "a-item",
        "z-item",
    ]
    proposal = first.proposals[0]
    assert proposal.proposal_kind == PROPOSAL_KIND
    assert proposal.payload_schema_ref == PAYLOAD_SCHEMA_REF
    assert proposal.payload_schema_version == PAYLOAD_SCHEMA_VERSION
    assert proposal.risk_code == "UNREVIEWED_EXTERNAL_FEED_ITEM"
    assert proposal.provenance_ref == artifact.raw_storage_ref
    assert proposal.payload == {
        "source_artifact_id": str(artifact.id),
        "feed_content_hash": artifact.content_hash,
        "feed_storage_ref": artifact.raw_storage_ref,
        "feed_format": "RSS_2_0",
        "feed_title": "Example News",
        "item_id": "a-item",
        "item_title": "First in deterministic order",
        "item_url": "https://www.example.test/news/a",
        "published_at": "2026-08-03T00:40:00+00:00",
        "summary_text": "Bounded first summary.",
    }
    assert first.output_metadata["proposal_count"] == 2


def test_atom_stage_extracts_alternate_link_summary_and_content() -> None:
    knowledge, evidence, artifact = _seed(
        ATOM_BODY,
        media_type="application/atom+xml",
    )
    result = FeedItemExtractionStageProcessor(
        knowledge=knowledge,
        evidence=evidence,
    ).process(
        run=_run(artifact),
        stage_code=STAGE_CODE,
        stage_version=STAGE_VERSION,
        input_hash=artifact.content_hash,
    )

    assert [proposal.payload["item_id"] for proposal in result.proposals] == [
        "urn:item:1",
        "urn:item:2",
    ]
    first, second = result.proposals
    assert first.payload["item_url"] is None
    assert first.payload["summary_text"] == "First atom content."
    assert second.payload["item_url"] == "https://www.example.test/atom/2"
    assert second.payload["summary_text"] == "Second atom summary."
    assert result.output_metadata["feed_format"] == "ATOM_1_0"


def test_duplicate_identity_and_source_mismatch_fail_closed() -> None:
    duplicate = RSS_BODY.replace(b"z-item", b"a-item")
    knowledge, evidence, artifact = _seed(
        duplicate,
        media_type="application/rss+xml",
    )
    processor = FeedItemExtractionStageProcessor(
        knowledge=knowledge,
        evidence=evidence,
    )
    with pytest.raises(FinalStageError) as duplicate_error:
        processor.process(
            run=_run(artifact),
            stage_code=STAGE_CODE,
            stage_version=STAGE_VERSION,
            input_hash=artifact.content_hash,
        )
    assert duplicate_error.value.code == "FEED_ITEM_DUPLICATE_IDENTITY"

    mismatched_run = _run(artifact)
    with pytest.raises(FinalStageError) as mismatch:
        processor.process(
            run=mismatched_run,
            stage_code=STAGE_CODE,
            stage_version=STAGE_VERSION,
            input_hash=canonical_content_hash(b"another"),
        )
    assert mismatch.value.code == "FEED_ITEM_SOURCE_ARTIFACT_MISMATCH"


def test_evidence_retryable_and_reference_integrity_are_mapped() -> None:
    knowledge, _, artifact = _seed(
        RSS_BODY,
        media_type="application/rss+xml",
    )
    retryable = FeedItemExtractionStageProcessor(
        knowledge=knowledge,
        evidence=RetryableReader(),  # type: ignore[arg-type]
    )
    with pytest.raises(RetryableStageError) as retryable_error:
        retryable.process(
            run=_run(artifact),
            stage_code=STAGE_CODE,
            stage_version=STAGE_VERSION,
            input_hash=artifact.content_hash,
        )
    assert retryable_error.value.code == "FEED_ITEM_EVIDENCE_RETRYABLE"

    bad_artifact = SourceArtifact.create(
        adapter_code=artifact.adapter_code,
        external_locator="https://feeds.example.test/bad-reference.xml",
        captured_at=artifact.captured_at,
        content_hash=artifact.content_hash,
        raw_storage_ref=canonical_storage_ref(canonical_content_hash(b"wrong")),
    )
    knowledge.add_source_artifact(bad_artifact)
    with pytest.raises(FinalStageError) as bad_reference:
        FeedItemExtractionStageProcessor(
            knowledge=knowledge,
            evidence=InMemoryRawSourceEvidenceStore(),
        ).process(
            run=_run(bad_artifact),
            stage_code=STAGE_CODE,
            stage_version=STAGE_VERSION,
            input_hash=bad_artifact.content_hash,
        )
    assert bad_reference.value.code == "FEED_ITEM_SOURCE_ARTIFACT_MISMATCH"


def test_parser_profile_and_stage_identity_are_exact() -> None:
    knowledge, evidence, artifact = _seed(
        RSS_BODY,
        media_type="application/rss+xml",
    )
    with pytest.raises(ValueError, match="proposal budget"):
        FeedItemExtractionStageProcessor(
            knowledge=knowledge,
            evidence=evidence,
            profile=StrictRssAtomParseProfile(max_items=257),
        )

    processor = FeedItemExtractionStageProcessor(
        knowledge=knowledge,
        evidence=evidence,
    )
    with pytest.raises(FinalStageError) as identity:
        processor.process(
            run=_run(artifact),
            stage_code="OTHER_STAGE",
            stage_version=STAGE_VERSION,
            input_hash=artifact.content_hash,
        )
    assert identity.value.code == "FEED_ITEM_STAGE_IDENTITY_INVALID"


def test_full_ingestion_worker_persists_proposals_without_review_or_materialization() -> None:
    knowledge, evidence, artifact = _seed(
        RSS_BODY,
        media_type="application/rss+xml",
    )
    repository = InMemoryIngestionOrchestrationRepository()
    orchestration = IngestionOrchestrationService(repository)
    lease_repository = InMemoryIngestionRunLeaseRepository(repository)
    leases = IngestionRunLeaseService(lease_repository)
    processor = FeedItemExtractionStageProcessor(
        knowledge=knowledge,
        evidence=evidence,
    )
    observer = InMemoryIngestionWorkerObserver()
    runner = IngestionWorkerRunner(
        repository=repository,
        orchestration=orchestration,
        leases=leases,
        registry=build_feed_item_extraction_runtime(processor),
        observer=observer,
        clock=lambda: NOW,
    )
    run = orchestration.start_run(
        input_artifact_kind=InputArtifactKind.SOURCE_ARTIFACT,
        input_artifact_id=artifact.id,
        input_content_hash=artifact.content_hash,
        pipeline_code=PIPELINE_CODE,
        pipeline_version=PIPELINE_VERSION,
        configuration_hash="sha256:feed-item-config",
    )

    result = runner.run_once(
        worker_ref="worker-feed-items",
        pipeline_code=PIPELINE_CODE,
        pipeline_version=PIPELINE_VERSION,
        ttl_seconds=60,
        trace_id="trace-feed-items",
    )

    assert result.outcome is IngestionWorkerRunOutcome.SUCCEEDED
    assert repository.get_run(run.id).state is IngestionRunState.SUCCEEDED
    proposals = repository.list_proposals(run.id)
    assert len(proposals) == 2
    assert all(proposal.proposal_kind == PROPOSAL_KIND for proposal in proposals)
    assert all(repository.get_review_decision(proposal.id) is None for proposal in proposals)
    assert all(repository.find_materialization(proposal.id) is None for proposal in proposals)
    assert observer.results[0].as_operational_dict()["error_code"] is None
    assert artifact.raw_storage_ref not in repr(
        observer.results[0].as_operational_dict()
    )
