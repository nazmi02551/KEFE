from __future__ import annotations

import json
from uuid import UUID

from sqlalchemy import Engine, text
from sqlalchemy.exc import IntegrityError

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


class PostgresKnowledgeRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def add_source_artifact(self, artifact: SourceArtifact) -> SourceArtifact:
        with self._engine.begin() as connection:
            inserted = connection.execute(
                text(
                    """
                    INSERT INTO knowledge.source_artifact (
                        id, adapter_code, external_locator, captured_at, content_hash,
                        external_id, canonical_url, publisher_or_issuer, published_at,
                        language_code, jurisdiction_code, raw_storage_ref
                    ) VALUES (
                        :id, :adapter_code, :external_locator, :captured_at, :content_hash,
                        :external_id, :canonical_url, :publisher_or_issuer, :published_at,
                        :language_code, :jurisdiction_code, :raw_storage_ref
                    )
                    ON CONFLICT (adapter_code, external_locator, content_hash) DO NOTHING
                    RETURNING id
                    """
                ),
                self._source_params(artifact),
            ).scalar_one_or_none()
            if inserted is not None:
                return artifact
            row = connection.execute(
                text(
                    """
                    SELECT * FROM knowledge.source_artifact
                    WHERE adapter_code = :adapter_code
                      AND external_locator = :external_locator
                      AND content_hash = :content_hash
                    """
                ),
                {
                    "adapter_code": artifact.adapter_code,
                    "external_locator": artifact.external_locator,
                    "content_hash": artifact.content_hash,
                },
            ).mappings().one()
            return self._source_from_row(row)

    def get_source_artifact(self, artifact_id: UUID) -> SourceArtifact | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                text("SELECT * FROM knowledge.source_artifact WHERE id = :id"),
                {"id": artifact_id},
            ).mappings().one_or_none()
        return self._source_from_row(row) if row else None

    def find_source_artifact(
        self,
        *,
        adapter_code: str,
        external_locator: str,
        content_hash: str,
    ) -> SourceArtifact | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT * FROM knowledge.source_artifact
                    WHERE adapter_code = :adapter_code
                      AND external_locator = :external_locator
                      AND content_hash = :content_hash
                    """
                ),
                {
                    "adapter_code": adapter_code,
                    "external_locator": external_locator,
                    "content_hash": content_hash,
                },
            ).mappings().one_or_none()
        return self._source_from_row(row) if row else None

    def add_normalized_artifact(self, artifact: NormalizedArtifact) -> None:
        self._insert(
            """
            INSERT INTO knowledge.normalized_artifact (
                id, source_artifact_id, artifact_kind, normalized_at, content_hash,
                text_content, language_code, jurisdiction_code, parent_artifact_id,
                reply_to_artifact_id, media_metadata
            ) VALUES (
                :id, :source_artifact_id, :artifact_kind, :normalized_at, :content_hash,
                :text_content, :language_code, :jurisdiction_code, :parent_artifact_id,
                :reply_to_artifact_id, CAST(:media_metadata AS jsonb)
            )
            """,
            {
                "id": artifact.id,
                "source_artifact_id": artifact.source_artifact_id,
                "artifact_kind": artifact.artifact_kind.value,
                "normalized_at": artifact.normalized_at,
                "content_hash": artifact.content_hash,
                "text_content": artifact.text,
                "language_code": artifact.language_code,
                "jurisdiction_code": artifact.jurisdiction_code,
                "parent_artifact_id": artifact.parent_artifact_id,
                "reply_to_artifact_id": artifact.reply_to_artifact_id,
                "media_metadata": json.dumps(artifact.media_metadata),
            },
        )

    def get_normalized_artifact(self, artifact_id: UUID) -> NormalizedArtifact | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                text("SELECT * FROM knowledge.normalized_artifact WHERE id = :id"),
                {"id": artifact_id},
            ).mappings().one_or_none()
        return self._normalized_from_row(row) if row else None

    def add_claim(self, claim: Claim) -> None:
        self._insert(
            """
            INSERT INTO knowledge.claim (id, normalized_text, language_code, created_at)
            VALUES (:id, :normalized_text, :language_code, :created_at)
            """,
            {
                "id": claim.id,
                "normalized_text": claim.normalized_text,
                "language_code": claim.language_code,
                "created_at": claim.created_at,
            },
        )

    def get_claim(self, claim_id: UUID) -> Claim | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                text("SELECT * FROM knowledge.claim WHERE id = :id"),
                {"id": claim_id},
            ).mappings().one_or_none()
        return self._claim_from_row(row) if row else None

    def add_claim_assessment(self, assessment: ClaimAssessment) -> None:
        self._insert(
            """
            INSERT INTO knowledge.claim_assessment (
                id, claim_id, claim_type, claim_state, taxonomy_version, review_state,
                assessed_at, methodology_version, reviewer_ref, rationale_code, provenance_ref
            ) VALUES (
                :id, :claim_id, :claim_type, :claim_state, :taxonomy_version, :review_state,
                :assessed_at, :methodology_version, :reviewer_ref, :rationale_code, :provenance_ref
            )
            """,
            {
                "id": assessment.id,
                "claim_id": assessment.claim_id,
                "claim_type": assessment.claim_type.value,
                "claim_state": assessment.claim_state.value,
                "taxonomy_version": assessment.taxonomy_version,
                "review_state": assessment.review_state.value,
                "assessed_at": assessment.assessed_at,
                "methodology_version": assessment.methodology_version,
                "reviewer_ref": assessment.reviewer_ref,
                "rationale_code": assessment.rationale_code,
                "provenance_ref": assessment.provenance_ref,
            },
        )

    def list_claim_assessments(self, claim_id: UUID) -> tuple[ClaimAssessment, ...]:
        rows = self._list(
            """
            SELECT * FROM knowledge.claim_assessment
            WHERE claim_id = :claim_id
            ORDER BY assessed_at, id
            """,
            {"claim_id": claim_id},
        )
        return tuple(self._assessment_from_row(row) for row in rows)

    def add_claim_assertion(self, assertion: ClaimAssertion) -> None:
        self._insert(
            """
            INSERT INTO knowledge.claim_assertion (
                id, claim_id, claimant_kind, claimant_ref, asserted_at,
                source_artifact_id, normalized_artifact_id, provenance_ref
            ) VALUES (
                :id, :claim_id, :claimant_kind, :claimant_ref, :asserted_at,
                :source_artifact_id, :normalized_artifact_id, :provenance_ref
            )
            """,
            {
                "id": assertion.id,
                "claim_id": assertion.claim_id,
                "claimant_kind": assertion.claimant_kind,
                "claimant_ref": assertion.claimant_ref,
                "asserted_at": assertion.asserted_at,
                "source_artifact_id": assertion.source_artifact_id,
                "normalized_artifact_id": assertion.normalized_artifact_id,
                "provenance_ref": assertion.provenance_ref,
            },
        )

    def list_claim_assertions(self, claim_id: UUID) -> tuple[ClaimAssertion, ...]:
        rows = self._list(
            """
            SELECT * FROM knowledge.claim_assertion
            WHERE claim_id = :claim_id
            ORDER BY asserted_at, id
            """,
            {"claim_id": claim_id},
        )
        return tuple(self._assertion_from_row(row) for row in rows)

    def add_evidence_link(self, link: EvidenceLink) -> None:
        source_id = (
            link.target_id if link.target_kind is EvidenceTargetKind.SOURCE_ARTIFACT else None
        )
        normalized_id = (
            link.target_id if link.target_kind is EvidenceTargetKind.NORMALIZED_ARTIFACT else None
        )
        self._insert(
            """
            INSERT INTO knowledge.evidence_link (
                id, claim_id, source_artifact_id, normalized_artifact_id,
                relation, review_state, provenance_ref, created_at
            ) VALUES (
                :id, :claim_id, :source_artifact_id, :normalized_artifact_id,
                :relation, :review_state, :provenance_ref, :created_at
            )
            """,
            {
                "id": link.id,
                "claim_id": link.claim_id,
                "source_artifact_id": source_id,
                "normalized_artifact_id": normalized_id,
                "relation": link.relation.value,
                "review_state": link.review_state.value,
                "provenance_ref": link.provenance_ref,
                "created_at": link.created_at,
            },
        )

    def list_evidence_links(self, claim_id: UUID) -> tuple[EvidenceLink, ...]:
        rows = self._list(
            """
            SELECT * FROM knowledge.evidence_link
            WHERE claim_id = :claim_id
            ORDER BY created_at, id
            """,
            {"claim_id": claim_id},
        )
        return tuple(self._evidence_from_row(row) for row in rows)

    def add_claim_relation(self, relation: ClaimRelation) -> None:
        self._insert(
            """
            INSERT INTO knowledge.claim_relation (
                id, from_claim_id, to_claim_id, relation_code, taxonomy_version,
                review_state, provenance_ref, created_at
            ) VALUES (
                :id, :from_claim_id, :to_claim_id, :relation_code, :taxonomy_version,
                :review_state, :provenance_ref, :created_at
            )
            """,
            {
                "id": relation.id,
                "from_claim_id": relation.from_claim_id,
                "to_claim_id": relation.to_claim_id,
                "relation_code": relation.relation_code,
                "taxonomy_version": relation.taxonomy_version,
                "review_state": relation.review_state.value,
                "provenance_ref": relation.provenance_ref,
                "created_at": relation.created_at,
            },
        )

    def list_claim_relations(self, claim_id: UUID) -> tuple[ClaimRelation, ...]:
        rows = self._list(
            """
            SELECT * FROM knowledge.claim_relation
            WHERE from_claim_id = :claim_id OR to_claim_id = :claim_id
            ORDER BY created_at, id
            """,
            {"claim_id": claim_id},
        )
        return tuple(self._claim_relation_from_row(row) for row in rows)

    def add_argument(self, argument: Argument) -> None:
        self._insert(
            """
            INSERT INTO knowledge.argument (
                id, body, language_code, review_state, normalized_artifact_id,
                source_artifact_id, author_or_claimant_ref, provenance_ref, created_at
            ) VALUES (
                :id, :body, :language_code, :review_state, :normalized_artifact_id,
                :source_artifact_id, :author_or_claimant_ref, :provenance_ref, :created_at
            )
            """,
            {
                "id": argument.id,
                "body": argument.body,
                "language_code": argument.language_code,
                "review_state": argument.review_state.value,
                "normalized_artifact_id": argument.normalized_artifact_id,
                "source_artifact_id": argument.source_artifact_id,
                "author_or_claimant_ref": argument.author_or_claimant_ref,
                "provenance_ref": argument.provenance_ref,
                "created_at": argument.created_at,
            },
        )

    def get_argument(self, argument_id: UUID) -> Argument | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                text("SELECT * FROM knowledge.argument WHERE id = :id"),
                {"id": argument_id},
            ).mappings().one_or_none()
        return self._argument_from_row(row) if row else None

    def add_argument_relation(self, relation: ArgumentRelation) -> None:
        targets = {
            "claim_target_id": None,
            "question_target_id": None,
            "argument_target_id": None,
        }
        targets[
            {
                ArgumentTargetKind.CLAIM: "claim_target_id",
                ArgumentTargetKind.QUESTION: "question_target_id",
                ArgumentTargetKind.ARGUMENT: "argument_target_id",
            }[relation.target_kind]
        ] = relation.target_ref
        self._insert(
            """
            INSERT INTO knowledge.argument_relation (
                id, argument_id, claim_target_id, question_target_id, argument_target_id,
                relation, taxonomy_version, review_state, provenance_ref, created_at
            ) VALUES (
                :id, :argument_id, :claim_target_id, :question_target_id, :argument_target_id,
                :relation, :taxonomy_version, :review_state, :provenance_ref, :created_at
            )
            """,
            {
                "id": relation.id,
                "argument_id": relation.argument_id,
                **targets,
                "relation": relation.relation.value,
                "taxonomy_version": relation.taxonomy_version,
                "review_state": relation.review_state.value,
                "provenance_ref": relation.provenance_ref,
                "created_at": relation.created_at,
            },
        )

    def list_argument_relations(self, argument_id: UUID) -> tuple[ArgumentRelation, ...]:
        rows = self._list(
            """
            SELECT * FROM knowledge.argument_relation
            WHERE argument_id = :argument_id
            ORDER BY created_at, id
            """,
            {"argument_id": argument_id},
        )
        return tuple(self._argument_relation_from_row(row) for row in rows)

    def _insert(self, statement: str, params: dict) -> None:
        try:
            with self._engine.begin() as connection:
                connection.execute(text(statement), params)
        except IntegrityError as exc:
            raise ValueError("knowledge persistence invariant violated") from exc

    def _list(self, statement: str, params: dict):
        with self._engine.connect() as connection:
            return connection.execute(text(statement), params).mappings().all()

    @staticmethod
    def _source_params(artifact: SourceArtifact) -> dict:
        return {
            "id": artifact.id,
            "adapter_code": artifact.adapter_code,
            "external_locator": artifact.external_locator,
            "captured_at": artifact.captured_at,
            "content_hash": artifact.content_hash,
            "external_id": artifact.external_id,
            "canonical_url": artifact.canonical_url,
            "publisher_or_issuer": artifact.publisher_or_issuer,
            "published_at": artifact.published_at,
            "language_code": artifact.language_code,
            "jurisdiction_code": artifact.jurisdiction_code,
            "raw_storage_ref": artifact.raw_storage_ref,
        }

    @staticmethod
    def _source_from_row(row) -> SourceArtifact:
        return SourceArtifact(
            id=row["id"],
            adapter_code=row["adapter_code"],
            external_locator=row["external_locator"],
            captured_at=row["captured_at"],
            content_hash=row["content_hash"],
            external_id=row["external_id"],
            canonical_url=row["canonical_url"],
            publisher_or_issuer=row["publisher_or_issuer"],
            published_at=row["published_at"],
            language_code=row["language_code"],
            jurisdiction_code=row["jurisdiction_code"],
            raw_storage_ref=row["raw_storage_ref"],
        )

    @staticmethod
    def _normalized_from_row(row) -> NormalizedArtifact:
        metadata = row["media_metadata"] or {}
        return NormalizedArtifact(
            id=row["id"],
            source_artifact_id=row["source_artifact_id"],
            artifact_kind=ArtifactKind(row["artifact_kind"]),
            normalized_at=row["normalized_at"],
            content_hash=row["content_hash"],
            text=row["text_content"],
            language_code=row["language_code"],
            jurisdiction_code=row["jurisdiction_code"],
            parent_artifact_id=row["parent_artifact_id"],
            reply_to_artifact_id=row["reply_to_artifact_id"],
            media_metadata=dict(metadata),
        )

    @staticmethod
    def _claim_from_row(row) -> Claim:
        return Claim(
            id=row["id"],
            normalized_text=row["normalized_text"],
            language_code=row["language_code"],
            created_at=row["created_at"],
        )

    @staticmethod
    def _assessment_from_row(row) -> ClaimAssessment:
        return ClaimAssessment(
            id=row["id"],
            claim_id=row["claim_id"],
            claim_type=ClaimType(row["claim_type"]),
            claim_state=ClaimState(row["claim_state"]),
            taxonomy_version=row["taxonomy_version"],
            review_state=ReviewState(row["review_state"]),
            assessed_at=row["assessed_at"],
            methodology_version=row["methodology_version"],
            reviewer_ref=row["reviewer_ref"],
            rationale_code=row["rationale_code"],
            provenance_ref=row["provenance_ref"],
        )

    @staticmethod
    def _assertion_from_row(row) -> ClaimAssertion:
        return ClaimAssertion(
            id=row["id"],
            claim_id=row["claim_id"],
            claimant_kind=row["claimant_kind"],
            claimant_ref=row["claimant_ref"],
            asserted_at=row["asserted_at"],
            source_artifact_id=row["source_artifact_id"],
            normalized_artifact_id=row["normalized_artifact_id"],
            provenance_ref=row["provenance_ref"],
        )

    @staticmethod
    def _evidence_from_row(row) -> EvidenceLink:
        source_id = row["source_artifact_id"]
        normalized_id = row["normalized_artifact_id"]
        return EvidenceLink(
            id=row["id"],
            claim_id=row["claim_id"],
            target_kind=(
                EvidenceTargetKind.SOURCE_ARTIFACT
                if source_id is not None
                else EvidenceTargetKind.NORMALIZED_ARTIFACT
            ),
            target_id=source_id if source_id is not None else normalized_id,
            relation=EvidenceRelation(row["relation"]),
            review_state=ReviewState(row["review_state"]),
            provenance_ref=row["provenance_ref"],
            created_at=row["created_at"],
        )

    @staticmethod
    def _claim_relation_from_row(row) -> ClaimRelation:
        return ClaimRelation(
            id=row["id"],
            from_claim_id=row["from_claim_id"],
            to_claim_id=row["to_claim_id"],
            relation_code=row["relation_code"],
            taxonomy_version=row["taxonomy_version"],
            review_state=ReviewState(row["review_state"]),
            provenance_ref=row["provenance_ref"],
            created_at=row["created_at"],
        )

    @staticmethod
    def _argument_from_row(row) -> Argument:
        return Argument(
            id=row["id"],
            body=row["body"],
            language_code=row["language_code"],
            review_state=ReviewState(row["review_state"]),
            normalized_artifact_id=row["normalized_artifact_id"],
            source_artifact_id=row["source_artifact_id"],
            author_or_claimant_ref=row["author_or_claimant_ref"],
            provenance_ref=row["provenance_ref"],
            created_at=row["created_at"],
        )

    @staticmethod
    def _argument_relation_from_row(row) -> ArgumentRelation:
        if row["claim_target_id"] is not None:
            target_kind = ArgumentTargetKind.CLAIM
            target_ref = row["claim_target_id"]
        elif row["question_target_id"] is not None:
            target_kind = ArgumentTargetKind.QUESTION
            target_ref = row["question_target_id"]
        else:
            target_kind = ArgumentTargetKind.ARGUMENT
            target_ref = row["argument_target_id"]
        return ArgumentRelation(
            id=row["id"],
            argument_id=row["argument_id"],
            target_kind=target_kind,
            target_ref=target_ref,
            relation=ArgumentRelationKind(row["relation"]),
            taxonomy_version=row["taxonomy_version"],
            review_state=ReviewState(row["review_state"]),
            provenance_ref=row["provenance_ref"],
            created_at=row["created_at"],
        )
