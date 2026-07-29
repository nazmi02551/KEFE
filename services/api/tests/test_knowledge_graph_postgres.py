from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text

from kefe_api.infrastructure.postgres_knowledge import PostgresKnowledgeRepository
from kefe_api.modules.knowledge.models import (
    Argument,
    ArgumentRelation,
    ArgumentRelationKind,
    ArgumentTargetKind,
    ArtifactKind,
    Claim,
    ClaimAssessment,
    ClaimAssertion,
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

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)


def test_postgres_knowledge_graph_round_trip_and_append_only_history() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    repository = PostgresKnowledgeRepository(engine)
    now = datetime.now(UTC)

    source = SourceArtifact.create(
        adapter_code="postgres-fixture",
        external_locator=f"https://example.test/{uuid4()}",
        content_hash="sha256:source-v1",
        publisher_or_issuer="Fixture Publisher",
        language_code="tr",
    )
    stored_source = repository.add_source_artifact(source)
    replay = repository.add_source_artifact(
        SourceArtifact.create(
            adapter_code=source.adapter_code,
            external_locator=source.external_locator,
            content_hash=source.content_hash,
        )
    )
    assert replay.id == stored_source.id
    assert repository.find_source_artifact(
        adapter_code=source.adapter_code,
        external_locator=source.external_locator,
        content_hash=source.content_hash,
    ) == stored_source

    normalized = NormalizedArtifact(
        id=uuid4(),
        source_artifact_id=source.id,
        artifact_kind=ArtifactKind.ORIGINAL_CONTENT,
        normalized_at=now,
        content_hash="sha256:normalized-v1",
        text="Normalize içerik",
        language_code="tr",
        media_metadata={"kind": "text"},
    )
    repository.add_normalized_artifact(normalized)
    assert repository.get_normalized_artifact(normalized.id) == normalized

    claim_a = Claim(id=uuid4(), normalized_text="Birinci iddia", language_code="tr")
    claim_b = Claim(id=uuid4(), normalized_text="İkinci iddia", language_code="tr")
    repository.add_claim(claim_a)
    repository.add_claim(claim_b)

    repository.add_claim_assertion(
        ClaimAssertion(
            id=uuid4(),
            claim_id=claim_a.id,
            claimant_kind="ORGANIZATION",
            claimant_ref="external:org:fixture",
            asserted_at=now,
            source_artifact_id=source.id,
            normalized_artifact_id=normalized.id,
        )
    )
    repository.add_claim_assessment(
        ClaimAssessment(
            id=uuid4(),
            claim_id=claim_a.id,
            claim_type=ClaimType.FACTUAL,
            claim_state=ClaimState.CLAIMED,
            taxonomy_version="claim-taxonomy-v1",
            review_state=ReviewState.ACCEPTED,
            assessed_at=now,
        )
    )
    repository.add_claim_assessment(
        ClaimAssessment(
            id=uuid4(),
            claim_id=claim_a.id,
            claim_type=ClaimType.FACTUAL,
            claim_state=ClaimState.SUPPORTED,
            taxonomy_version="claim-taxonomy-v1",
            review_state=ReviewState.ACCEPTED,
            assessed_at=now + timedelta(seconds=1),
        )
    )
    repository.add_evidence_link(
        EvidenceLink(
            id=uuid4(),
            claim_id=claim_a.id,
            target_kind=EvidenceTargetKind.NORMALIZED_ARTIFACT,
            target_id=normalized.id,
            relation=EvidenceRelation.SUPPORTS,
            review_state=ReviewState.ACCEPTED,
            created_at=now,
        )
    )
    repository.add_claim_relation(
        ClaimRelation(
            id=uuid4(),
            from_claim_id=claim_a.id,
            to_claim_id=claim_b.id,
            relation_code="QUALIFIES_SCOPE",
            taxonomy_version="claim-rel-v1",
            review_state=ReviewState.ACCEPTED,
            created_at=now,
        )
    )

    argument = Argument(
        id=uuid4(),
        body="İkinci iddianın kapsamını tartışan argüman.",
        language_code="tr",
        review_state=ReviewState.ACCEPTED,
        created_at=now,
        normalized_artifact_id=normalized.id,
        source_artifact_id=source.id,
    )
    repository.add_argument(argument)
    repository.add_argument_relation(
        ArgumentRelation(
            id=uuid4(),
            argument_id=argument.id,
            target_kind=ArgumentTargetKind.CLAIM,
            target_ref=claim_b.id,
            relation=ArgumentRelationKind.QUALIFIES,
            taxonomy_version="argument-rel-v1",
            review_state=ReviewState.ACCEPTED,
            created_at=now,
        )
    )

    assert repository.get_claim(claim_a.id) == claim_a
    assert [item.claim_state for item in repository.list_claim_assessments(claim_a.id)] == [
        ClaimState.CLAIMED,
        ClaimState.SUPPORTED,
    ]
    assert repository.list_claim_assertions(claim_a.id)[0].claimant_ref == (
        "external:org:fixture"
    )
    assert repository.list_evidence_links(claim_a.id)[0].relation is EvidenceRelation.SUPPORTS
    assert repository.list_claim_relations(claim_a.id)[0].to_claim_id == claim_b.id
    assert repository.get_argument(argument.id) == argument
    assert repository.list_argument_relations(argument.id)[0].target_ref == claim_b.id

    with engine.connect() as connection:
        assessment_count = connection.execute(
            text("SELECT count(*) FROM knowledge.claim_assessment WHERE claim_id = :claim_id"),
            {"claim_id": claim_a.id},
        ).scalar_one()
        source_count = connection.execute(
            text(
                """
                SELECT count(*) FROM knowledge.source_artifact
                WHERE adapter_code = :adapter_code
                  AND external_locator = :external_locator
                  AND content_hash = :content_hash
                """
            ),
            {
                "adapter_code": source.adapter_code,
                "external_locator": source.external_locator,
                "content_hash": source.content_hash,
            },
        ).scalar_one()

    assert assessment_count == 2
    assert source_count == 1
