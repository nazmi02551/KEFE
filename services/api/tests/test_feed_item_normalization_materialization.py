from __future__ import annotations

from datetime import UTC, datetime
from uuid import NAMESPACE_URL, uuid4, uuid5

import pytest

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
    ProposalReviewDecision,
    ProposalReviewDecisionKind,
    StageProcessorResult,
)
from kefe_api.modules.ingestion_orchestration.service import (
    IngestionOrchestrationService,
)
from kefe_api.modules.knowledge.in_memory import InMemoryKnowledgeRepository
from kefe_api.modules.knowledge.models import (
    ArtifactKind,
    NormalizedArtifact,
    SourceArtifact,
)
from kefe_api.modules.knowledge.source_evidence import (
    canonical_content_hash,
    canonical_storage_ref,
)


class FixedFeedItemProcessor:
    def __init__(self, payload: dict[str, object], *, provenance_ref: str) -> None:
        self._payload = payload
        self._provenance_ref = provenance_ref

    def process(self, **_) -> StageProcessorResult:
        return StageProcessorResult(
            proposals=(
                ProposalDraft(
                    proposal_kind="FEED_ITEM",
                    payload_schema_ref="kefe.feed-item",
                    payload_schema_version="1.0.0",
                    payload=self._payload,
                    configuration_version="feed-item-extraction-v1",
                    risk_code="UNREVIEWED_EXTERNAL_FEED_ITEM",
                    provenance_ref=self._provenance_ref,
                ),
            ),
            output_metadata={"fixture": "feed-item"},
        )


def _payload(
    source: SourceArtifact,
    *,
    overrides: dict[str, object] | None = None,
) -> dict[str, object]:
    values: dict[str, object] = {
        "source_artifact_id": str(source.id),
        "feed_content_hash": source.content_hash,
        "feed_storage_ref": source.raw_storage_ref,
        "feed_format": "RSS_2_0",
        "feed_title": "Fixture Feed",
        "item_id": "urn:fixture:item:2",
        "item_title": "Reviewed feed item title",
        "item_url": "https://news.example.test/items/2",
        "published_at": "2026-08-03T04:30:00+00:00",
        "summary_text": "Reviewed feed item summary.",
    }
    values.update(overrides or {})
    return values


def _fixture(
    *,
    overrides: dict[str, object] | None = None,
    provenance_ref: str | None = None,
):
    knowledge = InMemoryKnowledgeRepository()
    orchestration = InMemoryIngestionOrchestrationRepository()
    service = IngestionOrchestrationService(orchestration)
    content_hash = canonical_content_hash(b"immutable-feed-snapshot")
    source = knowledge.add_source_artifact(
        SourceArtifact.create(
            adapter_code="test.rss.v1",
            external_locator=f"https://feeds.example.test/{uuid4()}.xml",
            captured_at=datetime(2026, 8, 3, 4, 35, tzinfo=UTC),
            content_hash=content_hash,
            publisher_or_issuer="Fixture Feed",
            language_code="en",
            jurisdiction_code="GB",
            raw_storage_ref=canonical_storage_ref(content_hash),
        )
    )
    run = service.start_run(
        input_artifact_kind=InputArtifactKind.SOURCE_ARTIFACT,
        input_artifact_id=source.id,
        input_content_hash=source.content_hash,
        pipeline_code="RSS_ATOM_FEED_ITEM_EXTRACTION",
        pipeline_version="1.0.0",
        configuration_hash="sha256:feed-item-normalization-fixture",
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
        processor=FixedFeedItemProcessor(
            _payload(source, overrides=overrides),
            provenance_ref=provenance_ref or source.raw_storage_ref or "",
        ),
    )
    proposal = orchestration.list_proposals(run.id)[0]
    materializer = KnowledgeProposalMaterializer(
        knowledge_repository=knowledge,
        orchestration_repository=orchestration,
    )
    return service, orchestration, knowledge, source, proposal, materializer


def _accept(service: IngestionOrchestrationService, proposal_id):
    return service.review_proposal(
        proposal_id=proposal_id,
        decision=ProposalReviewDecisionKind.ACCEPTED,
        reviewer_ref="admin:feed-editor",
        rationale="Source and item fields checked.",
        reason_code="EDITORIAL_SOURCE_CHECKED",
        policy_version="feed-review-v1",
        risk_policy_version="external-content-risk-v1",
    )


def test_accepted_feed_item_materializes_deterministic_normalized_artifact() -> None:
    service, _, knowledge, source, proposal, materializer = _fixture()
    review = _accept(service, proposal.id)

    first = service.materialize_accepted_proposal(
        proposal_id=proposal.id,
        materializer=materializer,
    )
    replay = service.materialize_accepted_proposal(
        proposal_id=proposal.id,
        materializer=materializer,
    )

    assert replay == first
    assert first.target_kind == "NORMALIZED_ARTIFACT"
    assert first.target_id == uuid5(
        NAMESPACE_URL,
        f"kefe:proposal:{proposal.id}:NORMALIZED_ARTIFACT",
    )
    artifact = knowledge.get_normalized_artifact(first.target_id)
    assert artifact is not None
    assert artifact.source_artifact_id == source.id
    assert artifact.artifact_kind is ArtifactKind.EXTERNAL_EVIDENCE
    assert artifact.normalized_at == review.decided_at
    assert artifact.content_hash.startswith("sha256:")
    assert len(artifact.content_hash) == 71
    assert artifact.text == (
        "Reviewed feed item title\n\nReviewed feed item summary."
    )
    assert artifact.language_code == "en"
    assert artifact.jurisdiction_code == "GB"
    assert artifact.media_metadata["proposal_id"] == str(proposal.id)
    assert artifact.media_metadata["review_id"] == str(review.id)
    assert artifact.media_metadata["reviewer_ref"] == review.reviewer_ref
    assert artifact.media_metadata["feed_storage_ref"] == source.raw_storage_ref
    assert artifact.media_metadata["item_id"] == "urn:fixture:item:2"
    assert "raw_xml" not in artifact.media_metadata
    assert "headers" not in artifact.media_metadata
    assert "object_key" not in artifact.media_metadata


def test_missing_or_rejected_review_cannot_materialize_feed_item() -> None:
    service, _, _, _, proposal, materializer = _fixture()

    with pytest.raises(ValueError, match="ACCEPTED"):
        service.materialize_accepted_proposal(
            proposal_id=proposal.id,
            materializer=materializer,
        )

    service.review_proposal(
        proposal_id=proposal.id,
        decision=ProposalReviewDecisionKind.REJECTED,
        reviewer_ref="admin:feed-editor",
    )
    with pytest.raises(ValueError, match="ACCEPTED"):
        service.materialize_accepted_proposal(
            proposal_id=proposal.id,
            materializer=materializer,
        )


def test_materializer_defends_against_review_and_source_authority_drift() -> None:
    service, _, _, _, proposal, materializer = _fixture()
    review = _accept(service, proposal.id)

    wrong_review = ProposalReviewDecision(
        id=uuid4(),
        proposal_id=uuid4(),
        decision=ProposalReviewDecisionKind.ACCEPTED,
        reviewer_ref="admin:feed-editor",
        decided_at=review.decided_at,
    )
    with pytest.raises(ValueError, match="does not reference"):
        materializer.materialize(proposal=proposal, review=wrong_review)

    rejected_review = ProposalReviewDecision(
        id=uuid4(),
        proposal_id=proposal.id,
        decision=ProposalReviewDecisionKind.REJECTED,
        reviewer_ref="admin:feed-editor",
        decided_at=review.decided_at,
    )
    with pytest.raises(ValueError, match="requires ACCEPTED"):
        materializer.materialize(proposal=proposal, review=rejected_review)

    wrong_hash = canonical_content_hash(b"other-feed-snapshot")
    (
        bad_service,
        _,
        _,
        _,
        bad_proposal,
        bad_materializer,
    ) = _fixture(
        overrides={
            "feed_content_hash": wrong_hash,
            "feed_storage_ref": canonical_storage_ref(wrong_hash),
        },
        provenance_ref=canonical_storage_ref(wrong_hash),
    )
    _accept(bad_service, bad_proposal.id)
    with pytest.raises(ValueError, match="does not match SourceArtifact"):
        bad_service.materialize_accepted_proposal(
            proposal_id=bad_proposal.id,
            materializer=bad_materializer,
        )


@pytest.mark.parametrize(
    "overrides",
    [
        {"unexpected": "field"},
        {"item_title": " noncanonical"},
        {"item_url": "https://user:pass@news.example.test/items/2"},
        {"item_url": "https://news.example.test/items/2#fragment"},
        {"item_url": "https://news.example.test:8443/items/2"},
        {"published_at": "2026-08-03T07:30:00+03:00"},
        {"feed_format": "RSS_1_0"},
    ],
)
def test_feed_item_payload_validation_fails_closed(
    overrides: dict[str, object],
) -> None:
    service, _, _, _, proposal, materializer = _fixture(overrides=overrides)
    _accept(service, proposal.id)

    with pytest.raises(ValueError):
        service.materialize_accepted_proposal(
            proposal_id=proposal.id,
            materializer=materializer,
        )


def test_partial_success_retry_reuses_exact_target_and_rejects_conflict() -> None:
    service, orchestration, knowledge, source, proposal, materializer = _fixture()
    review = _accept(service, proposal.id)

    target_kind, target_id = materializer.materialize(
        proposal=proposal,
        review=review,
    )
    assert target_kind == "NORMALIZED_ARTIFACT"
    assert orchestration.find_materialization(proposal.id) is None

    recovered = service.materialize_accepted_proposal(
        proposal_id=proposal.id,
        materializer=materializer,
    )
    assert recovered.target_id == target_id
    assert knowledge.get_normalized_artifact(target_id) is not None

    (
        conflict_service,
        _,
        conflict_knowledge,
        conflict_source,
        conflict_proposal,
        conflict_materializer,
    ) = _fixture()
    _accept(conflict_service, conflict_proposal.id)
    conflict_id = uuid5(
        NAMESPACE_URL,
        f"kefe:proposal:{conflict_proposal.id}:NORMALIZED_ARTIFACT",
    )
    conflict_knowledge.add_normalized_artifact(
        NormalizedArtifact(
            id=conflict_id,
            source_artifact_id=conflict_source.id,
            artifact_kind=ArtifactKind.EXTERNAL_EVIDENCE,
            normalized_at=datetime(2026, 8, 3, 5, 0, tzinfo=UTC),
            content_hash="sha256:conflicting-record",
            text="Conflicting record",
            language_code=conflict_source.language_code,
            jurisdiction_code=conflict_source.jurisdiction_code,
            media_metadata={"conflict": True},
        )
    )

    with pytest.raises(ValueError, match="conflicting normalized artifact"):
        conflict_service.materialize_accepted_proposal(
            proposal_id=conflict_proposal.id,
            materializer=conflict_materializer,
        )

    assert source.raw_storage_ref is not None
