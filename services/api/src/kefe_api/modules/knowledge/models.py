from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4


class ClaimType(StrEnum):
    FACTUAL = "FACTUAL"
    CAUSAL = "CAUSAL"
    BEHAVIORAL = "BEHAVIORAL"
    MOTIVE = "MOTIVE"
    NORMATIVE = "NORMATIVE"
    LEGAL = "LEGAL"
    PROCESS = "PROCESS"
    PREDICTION = "PREDICTION"


class ClaimState(StrEnum):
    VERIFIED = "VERIFIED"
    SUPPORTED = "SUPPORTED"
    CLAIMED = "CLAIMED"
    DISPUTED = "DISPUTED"
    UNVERIFIED = "UNVERIFIED"
    UNRESOLVED = "UNRESOLVED"
    FALSE = "FALSE"


class ReviewState(StrEnum):
    PROPOSED = "PROPOSED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class EvidenceTargetKind(StrEnum):
    SOURCE_ARTIFACT = "SOURCE_ARTIFACT"
    NORMALIZED_ARTIFACT = "NORMALIZED_ARTIFACT"


class EvidenceRelation(StrEnum):
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    CONTEXTUALIZES = "CONTEXTUALIZES"


class ArgumentTargetKind(StrEnum):
    CLAIM = "CLAIM"
    QUESTION = "QUESTION"
    ARGUMENT = "ARGUMENT"


class ArgumentRelationKind(StrEnum):
    SUPPORTS = "SUPPORTS"
    OPPOSES = "OPPOSES"
    REBUTS = "REBUTS"
    QUALIFIES = "QUALIFIES"
    BRIDGES = "BRIDGES"


class ArtifactKind(StrEnum):
    ORIGINAL_CONTENT = "ORIGINAL_CONTENT"
    REPLY = "REPLY"
    EXTERNAL_EVIDENCE = "EXTERNAL_EVIDENCE"
    MEDIA = "MEDIA"
    OTHER = "OTHER"


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _require_text(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} must not be blank")


@dataclass(frozen=True, slots=True)
class SourceArtifact:
    id: UUID
    adapter_code: str
    external_locator: str
    captured_at: datetime
    content_hash: str
    external_id: str | None = None
    canonical_url: str | None = None
    publisher_or_issuer: str | None = None
    published_at: datetime | None = None
    language_code: str | None = None
    jurisdiction_code: str | None = None
    raw_storage_ref: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.adapter_code, "adapter_code")
        _require_text(self.external_locator, "external_locator")
        _require_text(self.content_hash, "content_hash")

    @property
    def ingestion_fingerprint(self) -> tuple[str, str, str]:
        return self.adapter_code, self.external_locator, self.content_hash

    @classmethod
    def create(
        cls,
        *,
        adapter_code: str,
        external_locator: str,
        content_hash: str,
        captured_at: datetime | None = None,
        **kwargs: Any,
    ) -> SourceArtifact:
        return cls(
            id=uuid4(),
            adapter_code=adapter_code,
            external_locator=external_locator,
            captured_at=captured_at or _utcnow(),
            content_hash=content_hash,
            **kwargs,
        )


@dataclass(frozen=True, slots=True)
class NormalizedArtifact:
    id: UUID
    source_artifact_id: UUID
    artifact_kind: ArtifactKind
    normalized_at: datetime
    content_hash: str
    text: str | None = None
    language_code: str | None = None
    jurisdiction_code: str | None = None
    parent_artifact_id: UUID | None = None
    reply_to_artifact_id: UUID | None = None
    media_metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_text(self.content_hash, "content_hash")
        if self.id == self.parent_artifact_id or self.id == self.reply_to_artifact_id:
            raise ValueError("normalized artifact cannot point to itself")


@dataclass(frozen=True, slots=True)
class Claim:
    id: UUID
    normalized_text: str
    language_code: str
    created_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        _require_text(self.normalized_text, "normalized_text")
        _require_text(self.language_code, "language_code")


@dataclass(frozen=True, slots=True)
class ClaimAssessment:
    id: UUID
    claim_id: UUID
    claim_type: ClaimType
    claim_state: ClaimState
    taxonomy_version: str
    review_state: ReviewState
    assessed_at: datetime
    methodology_version: str | None = None
    reviewer_ref: str | None = None
    rationale_code: str | None = None
    provenance_ref: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.taxonomy_version, "taxonomy_version")


@dataclass(frozen=True, slots=True)
class ClaimAssertion:
    id: UUID
    claim_id: UUID
    claimant_kind: str
    claimant_ref: str
    asserted_at: datetime
    source_artifact_id: UUID | None = None
    normalized_artifact_id: UUID | None = None
    provenance_ref: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.claimant_kind, "claimant_kind")
        _require_text(self.claimant_ref, "claimant_ref")


@dataclass(frozen=True, slots=True)
class EvidenceLink:
    id: UUID
    claim_id: UUID
    target_kind: EvidenceTargetKind
    target_id: UUID
    relation: EvidenceRelation
    review_state: ReviewState
    created_at: datetime
    provenance_ref: str | None = None


@dataclass(frozen=True, slots=True)
class ClaimRelation:
    id: UUID
    from_claim_id: UUID
    to_claim_id: UUID
    relation_code: str
    taxonomy_version: str
    review_state: ReviewState
    created_at: datetime
    provenance_ref: str | None = None

    def __post_init__(self) -> None:
        if self.from_claim_id == self.to_claim_id:
            raise ValueError("claim relation cannot target the same claim")
        _require_text(self.relation_code, "relation_code")
        _require_text(self.taxonomy_version, "taxonomy_version")


@dataclass(frozen=True, slots=True)
class Argument:
    id: UUID
    body: str
    language_code: str
    review_state: ReviewState
    created_at: datetime
    normalized_artifact_id: UUID | None = None
    source_artifact_id: UUID | None = None
    author_or_claimant_ref: str | None = None
    provenance_ref: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.body, "body")
        _require_text(self.language_code, "language_code")


@dataclass(frozen=True, slots=True)
class ArgumentRelation:
    id: UUID
    argument_id: UUID
    target_kind: ArgumentTargetKind
    target_ref: UUID
    relation: ArgumentRelationKind
    taxonomy_version: str
    review_state: ReviewState
    created_at: datetime
    provenance_ref: str | None = None

    def __post_init__(self) -> None:
        if self.target_kind is ArgumentTargetKind.ARGUMENT and self.argument_id == self.target_ref:
            raise ValueError("argument relation cannot target itself")
        _require_text(self.taxonomy_version, "taxonomy_version")
