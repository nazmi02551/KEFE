from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from kefe_api.modules.knowledge.in_memory import InMemoryKnowledgeRepository
from kefe_api.modules.knowledge.models import (
    Argument,
    ArgumentRelation,
    ArgumentRelationKind,
    ArgumentTargetKind,
    ArtifactKind,
    Claim,
    ClaimAssertion,
    ClaimAssessment,
    ClaimRelation,
    ClaimState,
    ClaimType,
    EvidenceLink,
    EvidenceRelation,
    EvidenceTargetKind,
    NormalizedArtifact,
    ReviewState,
    SourceArtifact,
)


def _source() -> SourceArtifact:
    return SourceArtifact.create(
        adapter_code="fixture",
        external_locator="https://example.test/item/1",
        content_hash="sha256:source-v1",
        publisher_or_issuer="Fixture Publisher",
        language_code="tr",
    )


def test_claim_assessment_history_is_append_only_and_separate_from_claimant() -> None:
    repository = InMemoryKnowledgeRepository()
    now = datetime.now(UTC)
    claim = Claim(id=uuid4(), normalized_text="Örnek iddia", language_code="tr")
    repository.add_claim(claim)

    repository.add_claim_assertion(
        ClaimAssertion(
            id=uuid4(),
            claim_id=claim.id,
            claimant_kind="ORGANIZATION",
            claimant_ref="external:org:1",
            asserted_at=now,
        )
    )
    repository.add_claim_assessment(
        ClaimAssessment(
            id=uuid4(),
            claim_id=claim.id,
            claim_type=ClaimType.FACTUAL,
            claim_state=ClaimState.CLAIMED,
            taxonomy_version="claim-taxonomy-v1",
            review_state=ReviewState.ACCEPTED,
            assessed_at=now,
            reviewer_ref="editor:one",
        )
    )
    repository.add_claim_assessment(
        ClaimAssessment(
            id=uuid4(),
            claim_id=claim.id,
            claim_type=ClaimType.FACTUAL,
            claim_state=ClaimState.SUPPORTED,
            taxonomy_version="claim-taxonomy-v1",
            review_state=ReviewState.ACCEPTED,
            assessed_at=now + timedelta(minutes=1),
            reviewer_ref="reviewer:two",
        )
    )

    assert repository.get_claim(claim.id) == claim
    assert [item.claim_state for item in repository.list_claim_assessments(claim.id)] == [
        ClaimState.CLAIMED,
        ClaimState.SUPPORTED,
    ]
    assertions = repository.list_claim_assertions(claim.id)
    assert assertions[0].claimant_ref == "external:org:1"
    assert len(repository.list_claim_assessments(claim.id)) == 2


def test_source_fingerprint_is_idempotent_and_normalized_artifact_keeps_lineage() -> None:
    repository = InMemoryKnowledgeRepository()
    source = _source()
    first = repository.add_source_artifact(source)
    replay = repository.add_source_artifact(
        SourceArtifact.create(
            adapter_code=source.adapter_code,
            external_locator=source.external_locator,
            content_hash=source.content_hash,
        )
    )

    assert replay.id == first.id

    normalized = NormalizedArtifact(
        id=uuid4(),
        source_artifact_id=first.id,
        artifact_kind=ArtifactKind.ORIGINAL_CONTENT,
        normalized_at=datetime.now(UTC),
        content_hash="sha256:normalized-v1",
        text="Normalize edilmiş içerik",
        language_code="tr",
    )
    repository.add_normalized_artifact(normalized)
    assert repository.get_normalized_artifact(normalized.id) == normalized


def test_evidence_link_does_not_create_or_mutate_claim_assessment() -> None:
    repository = InMemoryKnowledgeRepository()
    source = repository.add_source_artifact(_source())
    claim = Claim(id=uuid4(), normalized_text="Kanıt bekleyen iddia", language_code="tr")
    repository.add_claim(claim)

    link = EvidenceLink(
        id=uuid4(),
        claim_id=claim.id,
        target_kind=EvidenceTargetKind.SOURCE_ARTIFACT,
        target_id=source.id,
        relation=EvidenceRelation.SUPPORTS,
        review_state=ReviewState.ACCEPTED,
        created_at=datetime.now(UTC),
    )
    repository.add_evidence_link(link)

    assert repository.list_evidence_links(claim.id) == (link,)
    assert repository.list_claim_assessments(claim.id) == ()


def test_claim_and_argument_graph_preserve_distinct_relation_semantics() -> None:
    repository = InMemoryKnowledgeRepository()
    claim_a = Claim(id=uuid4(), normalized_text="A", language_code="tr")
    claim_b = Claim(id=uuid4(), normalized_text="B", language_code="tr")
    repository.add_claim(claim_a)
    repository.add_claim(claim_b)
    now = datetime.now(UTC)

    claim_relation = ClaimRelation(
        id=uuid4(),
        from_claim_id=claim_a.id,
        to_claim_id=claim_b.id,
        relation_code="NARROWS_SCOPE_OF",
        taxonomy_version="claim-rel-v1",
        review_state=ReviewState.ACCEPTED,
        created_at=now,
    )
    repository.add_claim_relation(claim_relation)

    argument = Argument(
        id=uuid4(),
        body="Bu argüman ikinci iddiayı nitelendirir.",
        language_code="tr",
        review_state=ReviewState.ACCEPTED,
        created_at=now,
    )
    repository.add_argument(argument)
    argument_relation = ArgumentRelation(
        id=uuid4(),
        argument_id=argument.id,
        target_kind=ArgumentTargetKind.CLAIM,
        target_ref=claim_b.id,
        relation=ArgumentRelationKind.QUALIFIES,
        taxonomy_version="argument-rel-v1",
        review_state=ReviewState.ACCEPTED,
        created_at=now,
    )
    repository.add_argument_relation(argument_relation)

    assert repository.list_claim_relations(claim_a.id) == (claim_relation,)
    assert repository.list_argument_relations(argument.id) == (argument_relation,)


def test_graph_self_edges_are_rejected_by_domain_model() -> None:
    claim_id = uuid4()
    with pytest.raises(ValueError, match="same claim"):
        ClaimRelation(
            id=uuid4(),
            from_claim_id=claim_id,
            to_claim_id=claim_id,
            relation_code="SAME_AS",
            taxonomy_version="v1",
            review_state=ReviewState.PROPOSED,
            created_at=datetime.now(UTC),
        )

    argument_id = uuid4()
    with pytest.raises(ValueError, match="target itself"):
        ArgumentRelation(
            id=uuid4(),
            argument_id=argument_id,
            target_kind=ArgumentTargetKind.ARGUMENT,
            target_ref=argument_id,
            relation=ArgumentRelationKind.REBUTS,
            taxonomy_version="v1",
            review_state=ReviewState.PROPOSED,
            created_at=datetime.now(UTC),
        )
