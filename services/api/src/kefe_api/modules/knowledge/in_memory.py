from __future__ import annotations

from copy import deepcopy
from threading import RLock
from uuid import UUID

from kefe_api.modules.knowledge.models import (
    Argument,
    ArgumentRelation,
    ArgumentTargetKind,
    Claim,
    ClaimAssessment,
    ClaimAssertion,
    ClaimRelation,
    EvidenceLink,
    EvidenceTargetKind,
    NormalizedArtifact,
    SourceArtifact,
)


class InMemoryKnowledgeRepository:
    def __init__(self) -> None:
        self._lock = RLock()
        self._source_artifacts: dict[UUID, SourceArtifact] = {}
        self._source_fingerprints: dict[tuple[str, str, str], UUID] = {}
        self._normalized_artifacts: dict[UUID, NormalizedArtifact] = {}
        self._claims: dict[UUID, Claim] = {}
        self._claim_assessments: dict[UUID, ClaimAssessment] = {}
        self._claim_assertions: dict[UUID, ClaimAssertion] = {}
        self._evidence_links: dict[UUID, EvidenceLink] = {}
        self._claim_relations: dict[UUID, ClaimRelation] = {}
        self._arguments: dict[UUID, Argument] = {}
        self._argument_relations: dict[UUID, ArgumentRelation] = {}

    @staticmethod
    def _insert_unique(store: dict[UUID, object], item_id: UUID, item: object) -> None:
        if item_id in store:
            raise ValueError("knowledge record already exists")
        store[item_id] = deepcopy(item)

    def add_source_artifact(self, artifact: SourceArtifact) -> SourceArtifact:
        with self._lock:
            existing_id = self._source_fingerprints.get(artifact.ingestion_fingerprint)
            if existing_id is not None:
                return deepcopy(self._source_artifacts[existing_id])
            self._insert_unique(self._source_artifacts, artifact.id, artifact)
            self._source_fingerprints[artifact.ingestion_fingerprint] = artifact.id
            return deepcopy(artifact)

    def get_source_artifact(self, artifact_id: UUID) -> SourceArtifact | None:
        with self._lock:
            item = self._source_artifacts.get(artifact_id)
            return deepcopy(item) if item else None

    def find_source_artifact(
        self,
        *,
        adapter_code: str,
        external_locator: str,
        content_hash: str,
    ) -> SourceArtifact | None:
        with self._lock:
            item_id = self._source_fingerprints.get(
                (adapter_code, external_locator, content_hash)
            )
            if item_id is None:
                return None
            return deepcopy(self._source_artifacts[item_id])

    def add_normalized_artifact(self, artifact: NormalizedArtifact) -> None:
        with self._lock:
            self._require_source(artifact.source_artifact_id)
            if artifact.parent_artifact_id is not None:
                self._require_normalized(artifact.parent_artifact_id)
            if artifact.reply_to_artifact_id is not None:
                self._require_normalized(artifact.reply_to_artifact_id)
            self._insert_unique(self._normalized_artifacts, artifact.id, artifact)

    def get_normalized_artifact(self, artifact_id: UUID) -> NormalizedArtifact | None:
        with self._lock:
            item = self._normalized_artifacts.get(artifact_id)
            return deepcopy(item) if item else None

    def add_claim(self, claim: Claim) -> None:
        with self._lock:
            self._insert_unique(self._claims, claim.id, claim)

    def get_claim(self, claim_id: UUID) -> Claim | None:
        with self._lock:
            item = self._claims.get(claim_id)
            return deepcopy(item) if item else None

    def add_claim_assessment(self, assessment: ClaimAssessment) -> None:
        with self._lock:
            self._require_claim(assessment.claim_id)
            self._insert_unique(self._claim_assessments, assessment.id, assessment)

    def list_claim_assessments(self, claim_id: UUID) -> tuple[ClaimAssessment, ...]:
        with self._lock:
            return tuple(
                deepcopy(item)
                for item in sorted(
                    (
                        assessment
                        for assessment in self._claim_assessments.values()
                        if assessment.claim_id == claim_id
                    ),
                    key=lambda item: (item.assessed_at, str(item.id)),
                )
            )

    def add_claim_assertion(self, assertion: ClaimAssertion) -> None:
        with self._lock:
            self._require_claim(assertion.claim_id)
            if assertion.source_artifact_id is not None:
                self._require_source(assertion.source_artifact_id)
            if assertion.normalized_artifact_id is not None:
                self._require_normalized(assertion.normalized_artifact_id)
            self._insert_unique(self._claim_assertions, assertion.id, assertion)

    def list_claim_assertions(self, claim_id: UUID) -> tuple[ClaimAssertion, ...]:
        with self._lock:
            return tuple(
                deepcopy(item)
                for item in sorted(
                    (
                        assertion
                        for assertion in self._claim_assertions.values()
                        if assertion.claim_id == claim_id
                    ),
                    key=lambda item: (item.asserted_at, str(item.id)),
                )
            )

    def add_evidence_link(self, link: EvidenceLink) -> None:
        with self._lock:
            self._require_claim(link.claim_id)
            if link.target_kind is EvidenceTargetKind.SOURCE_ARTIFACT:
                self._require_source(link.target_id)
            else:
                self._require_normalized(link.target_id)
            self._insert_unique(self._evidence_links, link.id, link)

    def list_evidence_links(self, claim_id: UUID) -> tuple[EvidenceLink, ...]:
        with self._lock:
            return tuple(
                deepcopy(item)
                for item in sorted(
                    (link for link in self._evidence_links.values() if link.claim_id == claim_id),
                    key=lambda item: (item.created_at, str(item.id)),
                )
            )

    def add_claim_relation(self, relation: ClaimRelation) -> None:
        with self._lock:
            self._require_claim(relation.from_claim_id)
            self._require_claim(relation.to_claim_id)
            self._insert_unique(self._claim_relations, relation.id, relation)

    def list_claim_relations(self, claim_id: UUID) -> tuple[ClaimRelation, ...]:
        with self._lock:
            return tuple(
                deepcopy(item)
                for item in sorted(
                    (
                        relation
                        for relation in self._claim_relations.values()
                        if relation.from_claim_id == claim_id or relation.to_claim_id == claim_id
                    ),
                    key=lambda item: (item.created_at, str(item.id)),
                )
            )

    def add_argument(self, argument: Argument) -> None:
        with self._lock:
            if argument.source_artifact_id is not None:
                self._require_source(argument.source_artifact_id)
            if argument.normalized_artifact_id is not None:
                self._require_normalized(argument.normalized_artifact_id)
            self._insert_unique(self._arguments, argument.id, argument)

    def get_argument(self, argument_id: UUID) -> Argument | None:
        with self._lock:
            item = self._arguments.get(argument_id)
            return deepcopy(item) if item else None

    def add_argument_relation(self, relation: ArgumentRelation) -> None:
        with self._lock:
            self._require_argument(relation.argument_id)
            if relation.target_kind is ArgumentTargetKind.CLAIM:
                self._require_claim(relation.target_ref)
            elif relation.target_kind is ArgumentTargetKind.ARGUMENT:
                self._require_argument(relation.target_ref)
            self._insert_unique(self._argument_relations, relation.id, relation)

    def list_argument_relations(self, argument_id: UUID) -> tuple[ArgumentRelation, ...]:
        with self._lock:
            return tuple(
                deepcopy(item)
                for item in sorted(
                    (
                        relation
                        for relation in self._argument_relations.values()
                        if relation.argument_id == argument_id
                    ),
                    key=lambda item: (item.created_at, str(item.id)),
                )
            )

    def _require_source(self, artifact_id: UUID) -> None:
        if artifact_id not in self._source_artifacts:
            raise KeyError(artifact_id)

    def _require_normalized(self, artifact_id: UUID) -> None:
        if artifact_id not in self._normalized_artifacts:
            raise KeyError(artifact_id)

    def _require_claim(self, claim_id: UUID) -> None:
        if claim_id not in self._claims:
            raise KeyError(claim_id)

    def _require_argument(self, argument_id: UUID) -> None:
        if argument_id not in self._arguments:
            raise KeyError(argument_id)
