from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlsplit
from uuid import UUID

from kefe_api.core.errors import DomainError
from kefe_api.modules.admin_security.feed_item_review import (
    FeedItemReviewRecord,
    SecuredFeedItemReviewService,
)
from kefe_api.modules.admin_security.models import AdminPrincipal
from kefe_api.modules.admin_security.proposal_queue import (
    ProposalQueuePage,
    SecuredProposalQueueService,
)
from kefe_api.modules.ingestion_orchestration.models import (
    InputArtifactKind,
    ProposalReviewDecisionKind,
)
from kefe_api.modules.ingestion_orchestration.review_queue import (
    ProposalQueueRecord,
    ProposalQueueReviewState,
)
from kefe_api.modules.ingestion_orchestration.service import FinalStageError
from kefe_api.modules.ingestion_orchestration.source_brief_ingestion import (
    CONFIGURATION_HASH,
    MAX_PUBLISHER_CHARS,
    MAX_SUMMARY_CHARS,
    MAX_TITLE_CHARS,
    MAX_URL_CHARS,
    PIPELINE_CODE,
    PIPELINE_VERSION,
    SOURCE_BRIEF_KIND,
    SOURCE_BRIEF_RISK_CODE,
    SOURCE_BRIEF_SCHEMA_REF,
    SOURCE_BRIEF_SCHEMA_VERSION,
    NormalizedFeedItemMetadata,
    require_source_brief_normalized_artifact,
)
from kefe_api.modules.knowledge.ports import KnowledgeRepository

_PAYLOAD_KEYS = frozenset(
    {
        "normalized_artifact_id",
        "parent_feed_item_proposal_id",
        "review_decision_id",
        "source_artifact_id",
        "source_content_hash",
        "evidence_ref",
        "feed_format",
        "publisher_or_issuer",
        "headline",
        "source_url",
        "published_at",
        "synopsis",
        "language_code",
        "jurisdiction_code",
    }
)


def _contract_invalid() -> DomainError:
    return DomainError(
        "ADMIN_SOURCE_BRIEF_CONTRACT_INVALID",
        "Source Brief record is inconsistent with its immutable lineage",
        409,
    )


def _required_text(value: Any, *, max_chars: int) -> str:
    if type(value) is not str:
        raise _contract_invalid()
    normalized = " ".join(value.split())
    if not normalized or normalized != value or len(value) > max_chars:
        raise _contract_invalid()
    return value


def _optional_text(value: Any, *, max_chars: int) -> str | None:
    if value is None:
        return None
    return _required_text(value, max_chars=max_chars)


def _uuid(value: Any) -> UUID:
    if type(value) is not str:
        raise _contract_invalid()
    try:
        parsed = UUID(value)
    except ValueError as exc:
        raise _contract_invalid() from exc
    if str(parsed) != value:
        raise _contract_invalid()
    return parsed


def _http_url(value: Any) -> str | None:
    if value is None:
        return None
    url = _required_text(value, max_chars=MAX_URL_CHARS)
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError as exc:
        raise _contract_invalid() from exc
    if parsed.scheme not in {"http", "https"}:
        raise _contract_invalid()
    if parsed.hostname is None or parsed.username is not None or parsed.password is not None:
        raise _contract_invalid()
    if parsed.fragment or port not in (None, 80, 443):
        raise _contract_invalid()
    return url


def _utc_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    if type(value) is not str:
        raise _contract_invalid()
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise _contract_invalid() from exc
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise _contract_invalid()
    if parsed.isoformat() != value:
        raise _contract_invalid()
    return parsed


@dataclass(frozen=True, slots=True)
class SourceBriefReviewPayload:
    normalized_artifact_id: UUID
    parent_feed_item_proposal_id: UUID
    review_decision_id: UUID
    source_artifact_id: UUID
    source_content_hash: str
    evidence_ref: str
    feed_format: str
    publisher_or_issuer: str | None
    headline: str
    source_url: str | None
    published_at: datetime | None
    synopsis: str | None
    language_code: str | None
    jurisdiction_code: str | None

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> SourceBriefReviewPayload:
        if type(payload) is not dict or frozenset(payload) != _PAYLOAD_KEYS:
            raise _contract_invalid()
        content_hash = _required_text(payload["source_content_hash"], max_chars=71)
        evidence_ref = _required_text(payload["evidence_ref"], max_chars=82)
        feed_format = _required_text(payload["feed_format"], max_chars=16)
        if feed_format not in {"RSS_2_0", "ATOM_1_0"}:
            raise _contract_invalid()
        return cls(
            normalized_artifact_id=_uuid(payload["normalized_artifact_id"]),
            parent_feed_item_proposal_id=_uuid(
                payload["parent_feed_item_proposal_id"]
            ),
            review_decision_id=_uuid(payload["review_decision_id"]),
            source_artifact_id=_uuid(payload["source_artifact_id"]),
            source_content_hash=content_hash,
            evidence_ref=evidence_ref,
            feed_format=feed_format,
            publisher_or_issuer=_optional_text(
                payload["publisher_or_issuer"],
                max_chars=MAX_PUBLISHER_CHARS,
            ),
            headline=_required_text(payload["headline"], max_chars=MAX_TITLE_CHARS),
            source_url=_http_url(payload["source_url"]),
            published_at=_utc_timestamp(payload["published_at"]),
            synopsis=_optional_text(payload["synopsis"], max_chars=MAX_SUMMARY_CHARS),
            language_code=_optional_text(payload["language_code"], max_chars=35),
            jurisdiction_code=_optional_text(
                payload["jurisdiction_code"],
                max_chars=35,
            ),
        )


@dataclass(frozen=True, slots=True)
class SourceBriefReviewRecord:
    queue_record: ProposalQueueRecord
    payload: SourceBriefReviewPayload
    normalized_metadata: NormalizedFeedItemMetadata
    parent_feed_item: FeedItemReviewRecord


@dataclass(frozen=True, slots=True)
class SourceBriefReviewPage:
    items: tuple[SourceBriefReviewRecord, ...]
    next_cursor: str | None


class SecuredSourceBriefReviewService:
    def __init__(
        self,
        *,
        queue: SecuredProposalQueueService,
        feed_items: SecuredFeedItemReviewService,
        knowledge: KnowledgeRepository,
    ) -> None:
        self._queue = queue
        self._feed_items = feed_items
        self._knowledge = knowledge

    def list_source_briefs(
        self,
        principal: AdminPrincipal,
        *,
        limit: int,
        cursor: str | None = None,
        review_state: ProposalQueueReviewState | None = None,
        run_id: UUID | None = None,
        now: datetime | None = None,
    ) -> SourceBriefReviewPage:
        page: ProposalQueuePage = self._queue.list_queue(
            principal,
            limit=limit,
            cursor=cursor,
            review_state=review_state,
            proposal_kind=SOURCE_BRIEF_KIND,
            risk_code=SOURCE_BRIEF_RISK_CODE,
            run_id=run_id,
            pipeline_code=PIPELINE_CODE,
            now=now,
        )
        return SourceBriefReviewPage(
            items=tuple(self._adapt(principal, record) for record in page.items),
            next_cursor=page.next_cursor,
        )

    def detail(
        self,
        principal: AdminPrincipal,
        proposal_id: UUID,
        *,
        now: datetime | None = None,
    ) -> SourceBriefReviewRecord:
        record = self._queue.detail(principal, proposal_id, now=now)
        if record.proposal.proposal_kind != SOURCE_BRIEF_KIND:
            raise DomainError(
                "ADMIN_SOURCE_BRIEF_NOT_FOUND",
                "Source Brief proposal not found",
                404,
            )
        return self._adapt(principal, record)

    def _adapt(
        self,
        principal: AdminPrincipal,
        record: ProposalQueueRecord,
    ) -> SourceBriefReviewRecord:
        proposal = record.proposal
        run = record.run
        if (
            proposal.proposal_kind != SOURCE_BRIEF_KIND
            or proposal.payload_schema_ref != SOURCE_BRIEF_SCHEMA_REF
            or proposal.payload_schema_version != SOURCE_BRIEF_SCHEMA_VERSION
            or proposal.risk_code != SOURCE_BRIEF_RISK_CODE
            or proposal.configuration_version != CONFIGURATION_HASH
            or proposal.configuration_version != run.configuration_hash
            or run.pipeline_code != PIPELINE_CODE
            or run.pipeline_version != PIPELINE_VERSION
            or run.input_artifact_kind is not InputArtifactKind.NORMALIZED_ARTIFACT
        ):
            raise _contract_invalid()

        payload = SourceBriefReviewPayload.from_mapping(proposal.payload)
        if (
            payload.normalized_artifact_id != run.input_artifact_id
            or proposal.provenance_ref != payload.evidence_ref
        ):
            raise _contract_invalid()

        normalized = self._knowledge.get_normalized_artifact(
            payload.normalized_artifact_id
        )
        if normalized is None or normalized.content_hash != run.input_content_hash:
            raise _contract_invalid()
        try:
            metadata = require_source_brief_normalized_artifact(normalized)
        except FinalStageError as exc:
            raise _contract_invalid() from exc

        parent = self._feed_items.detail(
            principal,
            payload.parent_feed_item_proposal_id,
            now=record.proposal.created_at,
        )
        parent_review = parent.queue_record.review
        if (
            parent_review is None
            or parent_review.id != payload.review_decision_id
            or parent_review.decision is not ProposalReviewDecisionKind.ACCEPTED
            or metadata.parent_feed_item_proposal_id
            != payload.parent_feed_item_proposal_id
            or metadata.review_decision_id != payload.review_decision_id
            or metadata.source_artifact_id != payload.source_artifact_id
            or metadata.feed_content_hash != payload.source_content_hash
            or metadata.feed_storage_ref != payload.evidence_ref
            or metadata.feed_format != payload.feed_format
            or metadata.publisher_or_issuer != payload.publisher_or_issuer
            or metadata.item_title != payload.headline
            or metadata.item_url != payload.source_url
            or metadata.published_at != payload.published_at
            or metadata.summary_text != payload.synopsis
            or normalized.source_artifact_id != payload.source_artifact_id
            or normalized.language_code != payload.language_code
            or normalized.jurisdiction_code != payload.jurisdiction_code
        ):
            raise _contract_invalid()
        return SourceBriefReviewRecord(
            queue_record=record,
            payload=payload,
            normalized_metadata=metadata,
            parent_feed_item=parent,
        )


__all__ = [
    "SecuredSourceBriefReviewService",
    "SourceBriefReviewPage",
    "SourceBriefReviewPayload",
    "SourceBriefReviewRecord",
]
