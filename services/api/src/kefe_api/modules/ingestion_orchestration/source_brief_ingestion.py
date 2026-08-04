from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any
from urllib.parse import urlsplit
from uuid import UUID

from kefe_api.modules.ingestion_orchestration.models import (
    IngestionRun,
    InputArtifactKind,
    ProposalDraft,
    StageProcessorResult,
)
from kefe_api.modules.ingestion_orchestration.service import FinalStageError
from kefe_api.modules.knowledge.models import ArtifactKind, NormalizedArtifact
from kefe_api.modules.knowledge.ports import KnowledgeRepository
from kefe_api.modules.knowledge.source_evidence import canonical_storage_ref

NORMALIZED_SCHEMA_REF = "kefe.normalized-feed-item"
NORMALIZED_SCHEMA_VERSION = "1.0.0"
PIPELINE_CODE = "FEED_ITEM_SOURCE_BRIEF"
PIPELINE_VERSION = "1.0.0"
STAGE_CODE = "BUILD_SOURCE_BRIEF"
STAGE_VERSION = "1.0.0"
SOURCE_BRIEF_KIND = "SOURCE_BRIEF"
SOURCE_BRIEF_SCHEMA_REF = "kefe.source-brief"
SOURCE_BRIEF_SCHEMA_VERSION = "1.0.0"
SOURCE_BRIEF_RISK_CODE = "UNREVIEWED_SOURCE_BRIEF"
CONFIGURATION_HASH = (
    "sha256:dcf3922e83b731768ba77ae675655f2aef8029ab5d8df93810998526ac53603a"
)

MAX_TITLE_CHARS = 4096
MAX_ITEM_ID_CHARS = 4096
MAX_URL_CHARS = 4096
MAX_SUMMARY_CHARS = 16_384
MAX_PUBLISHER_CHARS = 4096

_METADATA_KEYS = frozenset(
    {
        "schema_ref",
        "schema_version",
        "parent_feed_item_proposal_id",
        "review_decision_id",
        "source_artifact_id",
        "feed_content_hash",
        "feed_storage_ref",
        "feed_format",
        "feed_title",
        "publisher_or_issuer",
        "item_id",
        "item_title",
        "item_url",
        "published_at",
        "summary_text",
    }
)


def _fail(code: str) -> None:
    raise FinalStageError(code)


def _required_text(value: Any, *, max_chars: int) -> str:
    if type(value) is not str:
        _fail("SOURCE_BRIEF_NORMALIZED_ARTIFACT_INVALID")
    normalized = " ".join(value.split())
    if not normalized or normalized != value or len(value) > max_chars:
        _fail("SOURCE_BRIEF_NORMALIZED_ARTIFACT_INVALID")
    return value


def _optional_text(value: Any, *, max_chars: int) -> str | None:
    if value is None:
        return None
    return _required_text(value, max_chars=max_chars)


def _uuid(value: Any) -> UUID:
    if type(value) is not str:
        _fail("SOURCE_BRIEF_NORMALIZED_ARTIFACT_INVALID")
    try:
        parsed = UUID(value)
    except ValueError as exc:
        raise FinalStageError("SOURCE_BRIEF_NORMALIZED_ARTIFACT_INVALID") from exc
    if str(parsed) != value:
        _fail("SOURCE_BRIEF_NORMALIZED_ARTIFACT_INVALID")
    return parsed


def _http_url(value: Any) -> str | None:
    if value is None:
        return None
    url = _required_text(value, max_chars=MAX_URL_CHARS)
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError as exc:
        raise FinalStageError("SOURCE_BRIEF_NORMALIZED_ARTIFACT_INVALID") from exc
    if parsed.scheme not in {"http", "https"}:
        _fail("SOURCE_BRIEF_NORMALIZED_ARTIFACT_INVALID")
    if parsed.hostname is None or parsed.username is not None or parsed.password is not None:
        _fail("SOURCE_BRIEF_NORMALIZED_ARTIFACT_INVALID")
    if parsed.fragment or port not in (None, 80, 443):
        _fail("SOURCE_BRIEF_NORMALIZED_ARTIFACT_INVALID")
    return url


def _utc_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    if type(value) is not str:
        _fail("SOURCE_BRIEF_NORMALIZED_ARTIFACT_INVALID")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise FinalStageError("SOURCE_BRIEF_NORMALIZED_ARTIFACT_INVALID") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        _fail("SOURCE_BRIEF_NORMALIZED_ARTIFACT_INVALID")
    if parsed.isoformat() != value:
        _fail("SOURCE_BRIEF_NORMALIZED_ARTIFACT_INVALID")
    return parsed


def canonical_normalized_content_hash(metadata: dict[str, Any]) -> str:
    encoded = json.dumps(
        metadata,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return f"sha256:{sha256(encoded).hexdigest()}"


@dataclass(frozen=True, slots=True)
class NormalizedFeedItemMetadata:
    parent_feed_item_proposal_id: UUID
    review_decision_id: UUID
    source_artifact_id: UUID
    feed_content_hash: str
    feed_storage_ref: str
    feed_format: str
    feed_title: str
    publisher_or_issuer: str | None
    item_id: str
    item_title: str
    item_url: str | None
    published_at: datetime | None
    summary_text: str | None

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> NormalizedFeedItemMetadata:
        if type(value) is not dict or frozenset(value) != _METADATA_KEYS:
            _fail("SOURCE_BRIEF_NORMALIZED_ARTIFACT_INVALID")
        if value["schema_ref"] != NORMALIZED_SCHEMA_REF:
            _fail("SOURCE_BRIEF_NORMALIZED_ARTIFACT_INVALID")
        if value["schema_version"] != NORMALIZED_SCHEMA_VERSION:
            _fail("SOURCE_BRIEF_NORMALIZED_ARTIFACT_INVALID")
        content_hash = _required_text(value["feed_content_hash"], max_chars=71)
        storage_ref = _required_text(value["feed_storage_ref"], max_chars=82)
        try:
            if canonical_storage_ref(content_hash) != storage_ref:
                _fail("SOURCE_BRIEF_NORMALIZED_ARTIFACT_INVALID")
        except ValueError as exc:
            raise FinalStageError("SOURCE_BRIEF_NORMALIZED_ARTIFACT_INVALID") from exc
        feed_format = _required_text(value["feed_format"], max_chars=16)
        if feed_format not in {"RSS_2_0", "ATOM_1_0"}:
            _fail("SOURCE_BRIEF_NORMALIZED_ARTIFACT_INVALID")
        return cls(
            parent_feed_item_proposal_id=_uuid(value["parent_feed_item_proposal_id"]),
            review_decision_id=_uuid(value["review_decision_id"]),
            source_artifact_id=_uuid(value["source_artifact_id"]),
            feed_content_hash=content_hash,
            feed_storage_ref=storage_ref,
            feed_format=feed_format,
            feed_title=_required_text(value["feed_title"], max_chars=MAX_TITLE_CHARS),
            publisher_or_issuer=_optional_text(
                value["publisher_or_issuer"],
                max_chars=MAX_PUBLISHER_CHARS,
            ),
            item_id=_required_text(value["item_id"], max_chars=MAX_ITEM_ID_CHARS),
            item_title=_required_text(value["item_title"], max_chars=MAX_TITLE_CHARS),
            item_url=_http_url(value["item_url"]),
            published_at=_utc_timestamp(value["published_at"]),
            summary_text=_optional_text(value["summary_text"], max_chars=MAX_SUMMARY_CHARS),
        )

    def as_mapping(self) -> dict[str, Any]:
        return {
            "schema_ref": NORMALIZED_SCHEMA_REF,
            "schema_version": NORMALIZED_SCHEMA_VERSION,
            "parent_feed_item_proposal_id": str(self.parent_feed_item_proposal_id),
            "review_decision_id": str(self.review_decision_id),
            "source_artifact_id": str(self.source_artifact_id),
            "feed_content_hash": self.feed_content_hash,
            "feed_storage_ref": self.feed_storage_ref,
            "feed_format": self.feed_format,
            "feed_title": self.feed_title,
            "publisher_or_issuer": self.publisher_or_issuer,
            "item_id": self.item_id,
            "item_title": self.item_title,
            "item_url": self.item_url,
            "published_at": self.published_at.isoformat() if self.published_at is not None else None,
            "summary_text": self.summary_text,
        }


class SourceBriefStageProcessor:
    def __init__(self, knowledge: KnowledgeRepository) -> None:
        self._knowledge = knowledge

    def process(
        self,
        *,
        run: IngestionRun,
        stage_code: str,
        stage_version: str,
        input_hash: str,
    ) -> StageProcessorResult:
        if stage_code != STAGE_CODE or stage_version != STAGE_VERSION:
            _fail("SOURCE_BRIEF_STAGE_IDENTITY_INVALID")
        if run.pipeline_code != PIPELINE_CODE or run.pipeline_version != PIPELINE_VERSION:
            _fail("SOURCE_BRIEF_PIPELINE_IDENTITY_INVALID")
        if run.configuration_hash != CONFIGURATION_HASH:
            _fail("SOURCE_BRIEF_CONFIGURATION_INVALID")
        if run.input_artifact_kind is not InputArtifactKind.NORMALIZED_ARTIFACT:
            _fail("SOURCE_BRIEF_INPUT_KIND_INVALID")
        if input_hash != run.input_content_hash:
            _fail("SOURCE_BRIEF_INPUT_HASH_MISMATCH")

        artifact = self._knowledge.get_normalized_artifact(run.input_artifact_id)
        if artifact is None:
            _fail("SOURCE_BRIEF_NORMALIZED_ARTIFACT_NOT_FOUND")
        if artifact.id != run.input_artifact_id or artifact.content_hash != input_hash:
            _fail("SOURCE_BRIEF_INPUT_HASH_MISMATCH")
        if artifact.artifact_kind is not ArtifactKind.EXTERNAL_EVIDENCE:
            _fail("SOURCE_BRIEF_NORMALIZED_ARTIFACT_INVALID")
        metadata = NormalizedFeedItemMetadata.from_mapping(artifact.media_metadata)
        if canonical_normalized_content_hash(metadata.as_mapping()) != artifact.content_hash:
            _fail("SOURCE_BRIEF_NORMALIZED_ARTIFACT_INVALID")
        if metadata.source_artifact_id != artifact.source_artifact_id:
            _fail("SOURCE_BRIEF_NORMALIZED_ARTIFACT_INVALID")

        source = self._knowledge.get_source_artifact(metadata.source_artifact_id)
        if source is None:
            _fail("SOURCE_BRIEF_SOURCE_ARTIFACT_NOT_FOUND")
        if source.content_hash != metadata.feed_content_hash or source.raw_storage_ref != metadata.feed_storage_ref:
            _fail("SOURCE_BRIEF_SOURCE_ARTIFACT_MISMATCH")

        payload = {
            "normalized_artifact_id": str(artifact.id),
            "parent_feed_item_proposal_id": str(metadata.parent_feed_item_proposal_id),
            "review_decision_id": str(metadata.review_decision_id),
            "source_artifact_id": str(metadata.source_artifact_id),
            "source_content_hash": metadata.feed_content_hash,
            "evidence_ref": metadata.feed_storage_ref,
            "feed_format": metadata.feed_format,
            "publisher_or_issuer": metadata.publisher_or_issuer,
            "headline": metadata.item_title,
            "source_url": metadata.item_url,
            "published_at": metadata.published_at.isoformat() if metadata.published_at is not None else None,
            "synopsis": metadata.summary_text,
            "language_code": artifact.language_code,
            "jurisdiction_code": artifact.jurisdiction_code,
        }
        return StageProcessorResult(
            proposals=(
                ProposalDraft(
                    proposal_kind=SOURCE_BRIEF_KIND,
                    payload_schema_ref=SOURCE_BRIEF_SCHEMA_REF,
                    payload_schema_version=SOURCE_BRIEF_SCHEMA_VERSION,
                    payload=payload,
                    configuration_version=CONFIGURATION_HASH,
                    risk_code=SOURCE_BRIEF_RISK_CODE,
                    provenance_ref=metadata.feed_storage_ref,
                ),
            ),
            output_metadata={
                "normalized_artifact_id": str(artifact.id),
                "parent_feed_item_proposal_id": str(metadata.parent_feed_item_proposal_id),
                "source_artifact_id": str(metadata.source_artifact_id),
                "proposal_kind": SOURCE_BRIEF_KIND,
            },
        )


def require_source_brief_normalized_artifact(
    artifact: NormalizedArtifact,
) -> NormalizedFeedItemMetadata:
    if artifact.artifact_kind is not ArtifactKind.EXTERNAL_EVIDENCE:
        _fail("SOURCE_BRIEF_NORMALIZED_ARTIFACT_INVALID")
    metadata = NormalizedFeedItemMetadata.from_mapping(artifact.media_metadata)
    if artifact.content_hash != canonical_normalized_content_hash(metadata.as_mapping()):
        _fail("SOURCE_BRIEF_NORMALIZED_ARTIFACT_INVALID")
    if artifact.source_artifact_id != metadata.source_artifact_id:
        _fail("SOURCE_BRIEF_NORMALIZED_ARTIFACT_INVALID")
    return metadata


__all__ = [
    "CONFIGURATION_HASH",
    "NORMALIZED_SCHEMA_REF",
    "NORMALIZED_SCHEMA_VERSION",
    "NormalizedFeedItemMetadata",
    "PIPELINE_CODE",
    "PIPELINE_VERSION",
    "SOURCE_BRIEF_KIND",
    "SOURCE_BRIEF_RISK_CODE",
    "SOURCE_BRIEF_SCHEMA_REF",
    "SOURCE_BRIEF_SCHEMA_VERSION",
    "STAGE_CODE",
    "STAGE_VERSION",
    "SourceBriefStageProcessor",
    "canonical_normalized_content_hash",
    "require_source_brief_normalized_artifact",
]
