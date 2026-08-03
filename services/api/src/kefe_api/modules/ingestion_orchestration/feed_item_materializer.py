from __future__ import annotations

import re
from datetime import UTC, datetime
from hashlib import sha256
from urllib.parse import urlsplit
from uuid import NAMESPACE_URL, UUID, uuid5

from kefe_api.modules.ingestion_orchestration.feed_item_extraction import (
    PAYLOAD_SCHEMA_REF,
    PAYLOAD_SCHEMA_VERSION,
    PROPOSAL_KIND,
)
from kefe_api.modules.ingestion_orchestration.models import (
    Proposal,
    ProposalReviewDecision,
    ProposalReviewDecisionKind,
)
from kefe_api.modules.knowledge.models import (
    ArtifactKind,
    NormalizedArtifact,
    SourceArtifact,
)
from kefe_api.modules.knowledge.ports import KnowledgeRepository
from kefe_api.modules.knowledge.source_evidence import canonical_storage_ref

TARGET_KIND = "NORMALIZED_ARTIFACT"
NORMALIZED_SCHEMA_REF = "kefe.normalized-feed-item"
NORMALIZED_SCHEMA_VERSION = "1.0.0"

MAX_ITEM_ID_CHARS = 4096
MAX_TITLE_CHARS = 4096
MAX_SUMMARY_CHARS = 16_384
MAX_NORMALIZED_TEXT_CHARS = MAX_TITLE_CHARS + 2 + MAX_SUMMARY_CHARS
MAX_URL_CHARS = 4096
MAX_REVIEWER_REF_CHARS = 512
MAX_PROVENANCE_CHARS = 4096

_SHA256_HASH = re.compile(r"^sha256:[0-9a-f]{64}$")
_PAYLOAD_FIELDS = frozenset(
    {
        "source_artifact_id",
        "feed_content_hash",
        "feed_storage_ref",
        "feed_format",
        "feed_title",
        "item_id",
        "item_title",
        "item_url",
        "published_at",
        "summary_text",
    }
)


def _require_utc(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValueError(f"{field_name} must be timezone-aware UTC")


def _canonical_text(
    value: object,
    *,
    field_name: str,
    max_chars: int,
    required: bool,
) -> str | None:
    if value is None:
        if required:
            raise ValueError(f"{field_name} is required")
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be text")
    normalized = " ".join(value.split())
    if not normalized:
        if required:
            raise ValueError(f"{field_name} must not be blank")
        return None
    if normalized != value or len(normalized) > max_chars:
        raise ValueError(f"{field_name} must be canonical bounded text")
    return normalized


def _canonical_uuid(value: object, field_name: str) -> UUID:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be canonical UUID text")
    try:
        parsed = UUID(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be canonical UUID text") from exc
    if str(parsed) != value:
        raise ValueError(f"{field_name} must be canonical UUID text")
    return parsed


def _canonical_url(value: object) -> str | None:
    if value is None:
        return None
    text = _canonical_text(
        value,
        field_name="item_url",
        max_chars=MAX_URL_CHARS,
        required=True,
    )
    assert text is not None
    try:
        parsed = urlsplit(text)
        port = parsed.port
    except ValueError as exc:
        raise ValueError("item_url is invalid") from exc
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("item_url is invalid")
    if parsed.hostname is None or parsed.username is not None or parsed.password is not None:
        raise ValueError("item_url is invalid")
    if parsed.fragment or port not in (None, 80, 443):
        raise ValueError("item_url is invalid")
    return text


def _canonical_timestamp(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or len(value) > 64:
        raise ValueError("published_at must be canonical UTC ISO-8601 text")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("published_at must be canonical UTC ISO-8601 text") from exc
    _require_utc(parsed, "published_at")
    if parsed.isoformat() != value:
        raise ValueError("published_at must be canonical UTC ISO-8601 text")
    return value


class FeedItemProposalMaterializer:
    def __init__(self, *, knowledge_repository: KnowledgeRepository) -> None:
        self._knowledge = knowledge_repository

    def materialize(
        self,
        *,
        proposal: Proposal,
        review: ProposalReviewDecision,
    ) -> tuple[str, UUID]:
        if type(proposal) is not Proposal or type(review) is not ProposalReviewDecision:
            raise ValueError("feed item materialization requires exact proposal records")
        if review.proposal_id != proposal.id:
            raise ValueError("feed item review does not match proposal")
        if review.decision is not ProposalReviewDecisionKind.ACCEPTED:
            raise ValueError("feed item materialization requires ACCEPTED review")
        _require_utc(review.decided_at, "review.decided_at")
        reviewer_ref = _canonical_text(
            review.reviewer_ref,
            field_name="reviewer_ref",
            max_chars=MAX_REVIEWER_REF_CHARS,
            required=True,
        )
        assert reviewer_ref is not None
        self._require_proposal_identity(proposal)
        payload = proposal.payload
        if type(payload) is not dict or frozenset(payload) != _PAYLOAD_FIELDS:
            raise ValueError("feed item payload fields are invalid")

        source_id = _canonical_uuid(payload["source_artifact_id"], "source_artifact_id")
        source = self._knowledge.get_source_artifact(source_id)
        if source is None:
            raise ValueError("feed item source artifact is missing")
        self._require_source_lineage(source=source, payload=payload)

        feed_format = _canonical_text(
            payload["feed_format"],
            field_name="feed_format",
            max_chars=16,
            required=True,
        )
        if feed_format not in {"ATOM_1_0", "RSS_2_0"}:
            raise ValueError("feed_format is invalid")
        feed_title = _canonical_text(
            payload["feed_title"],
            field_name="feed_title",
            max_chars=MAX_TITLE_CHARS,
            required=True,
        )
        item_id = _canonical_text(
            payload["item_id"],
            field_name="item_id",
            max_chars=MAX_ITEM_ID_CHARS,
            required=True,
        )
        item_title = _canonical_text(
            payload["item_title"],
            field_name="item_title",
            max_chars=MAX_TITLE_CHARS,
            required=True,
        )
        summary = _canonical_text(
            payload["summary_text"],
            field_name="summary_text",
            max_chars=MAX_SUMMARY_CHARS,
            required=False,
        )
        item_url = _canonical_url(payload["item_url"])
        published_at = _canonical_timestamp(payload["published_at"])
        assert feed_title is not None and item_id is not None and item_title is not None

        canonical_text = item_title if summary is None else f"{item_title}\n\n{summary}"
        if len(canonical_text) > MAX_NORMALIZED_TEXT_CHARS:
            raise ValueError("normalized feed item text exceeds the supported budget")
        target_id = uuid5(
            NAMESPACE_URL,
            f"kefe:proposal:{proposal.id}:{TARGET_KIND}",
        )
        provenance_ref = self._provenance(proposal=proposal, review=review)
        artifact = NormalizedArtifact(
            id=target_id,
            source_artifact_id=source.id,
            artifact_kind=ArtifactKind.EXTERNAL_EVIDENCE,
            normalized_at=review.decided_at,
            content_hash=f"sha256:{sha256(canonical_text.encode('utf-8')).hexdigest()}",
            text=canonical_text,
            language_code=source.language_code,
            jurisdiction_code=source.jurisdiction_code,
            media_metadata={
                "schema_ref": NORMALIZED_SCHEMA_REF,
                "schema_version": NORMALIZED_SCHEMA_VERSION,
                "feed_format": feed_format,
                "feed_title": feed_title,
                "item_id": item_id,
                "item_url": item_url,
                "published_at": published_at,
                "proposal_id": str(proposal.id),
                "review_id": str(review.id),
                "reviewer_ref": reviewer_ref,
                "provenance_ref": provenance_ref,
            },
        )
        self._add_exact(artifact)
        return TARGET_KIND, target_id

    @staticmethod
    def _require_proposal_identity(proposal: Proposal) -> None:
        if proposal.proposal_kind != PROPOSAL_KIND:
            raise ValueError("proposal kind is not FEED_ITEM")
        if proposal.payload_schema_ref != PAYLOAD_SCHEMA_REF:
            raise ValueError("FEED_ITEM payload schema reference drifted")
        if proposal.payload_schema_version != PAYLOAD_SCHEMA_VERSION:
            raise ValueError("FEED_ITEM payload schema version drifted")

    @staticmethod
    def _require_source_lineage(
        *,
        source: SourceArtifact,
        payload: dict[str, object],
    ) -> None:
        feed_content_hash = payload["feed_content_hash"]
        if not isinstance(feed_content_hash, str) or _SHA256_HASH.fullmatch(
            feed_content_hash
        ) is None:
            raise ValueError("feed_content_hash must be canonical SHA-256")
        if source.content_hash != feed_content_hash:
            raise ValueError("feed item content hash does not match source artifact")
        feed_storage_ref = payload["feed_storage_ref"]
        if not isinstance(feed_storage_ref, str):
            raise ValueError("feed_storage_ref is invalid")
        if source.raw_storage_ref is None or source.raw_storage_ref != feed_storage_ref:
            raise ValueError("feed item storage reference does not match source artifact")
        if canonical_storage_ref(source.content_hash) != source.raw_storage_ref:
            raise ValueError("source artifact evidence reference is invalid")

    @staticmethod
    def _provenance(
        *,
        proposal: Proposal,
        review: ProposalReviewDecision,
    ) -> str:
        value = f"proposal:{proposal.id};review:{review.id}"
        if len(value) > MAX_PROVENANCE_CHARS:
            raise ValueError("feed item provenance exceeds the supported budget")
        return value

    def _add_exact(self, artifact: NormalizedArtifact) -> None:
        existing = self._knowledge.get_normalized_artifact(artifact.id)
        if existing is not None:
            if existing != artifact:
                raise ValueError("normalized feed item target conflicts with existing record")
            return
        try:
            self._knowledge.add_normalized_artifact(artifact)
        except ValueError:
            existing = self._knowledge.get_normalized_artifact(artifact.id)
            if existing == artifact:
                return
            raise


__all__ = [
    "FeedItemProposalMaterializer",
    "NORMALIZED_SCHEMA_REF",
    "NORMALIZED_SCHEMA_VERSION",
    "TARGET_KIND",
]
