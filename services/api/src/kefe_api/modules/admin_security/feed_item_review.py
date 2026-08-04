from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlsplit
from uuid import UUID

from kefe_api.core.errors import DomainError
from kefe_api.modules.admin_security.models import AdminPrincipal
from kefe_api.modules.admin_security.proposal_queue import (
    ProposalQueuePage,
    SecuredProposalQueueService,
)
from kefe_api.modules.ingestion_orchestration.feed_item_extraction import (
    MAX_ITEM_ID_CHARS,
    MAX_ITEM_TITLE_CHARS,
    MAX_ITEM_URL_CHARS,
    MAX_SUMMARY_CHARS,
    PAYLOAD_SCHEMA_REF,
    PAYLOAD_SCHEMA_VERSION,
    PIPELINE_CODE,
    PIPELINE_VERSION,
    PROPOSAL_KIND,
    RISK_CODE,
)
from kefe_api.modules.ingestion_orchestration.models import InputArtifactKind
from kefe_api.modules.ingestion_orchestration.review_queue import (
    ProposalQueueRecord,
    ProposalQueueReviewState,
)
from kefe_api.modules.knowledge.ports import KnowledgeRepository
from kefe_api.modules.knowledge.source_evidence import canonical_storage_ref

_PAYLOAD_KEYS = frozenset(
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
_ALLOWED_FORMATS = frozenset({"RSS_2_0", "ATOM_1_0"})


def _contract_invalid() -> DomainError:
    return DomainError(
        "ADMIN_FEED_ITEM_CONTRACT_INVALID",
        "Feed item review record is inconsistent with its immutable source",
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
    url = _required_text(value, max_chars=MAX_ITEM_URL_CHARS)
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
class FeedItemReviewPayload:
    source_artifact_id: UUID
    feed_content_hash: str
    feed_storage_ref: str
    feed_format: str
    feed_title: str
    item_id: str
    item_title: str
    item_url: str | None
    published_at: datetime | None
    summary_text: str | None

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> FeedItemReviewPayload:
        if type(payload) is not dict or frozenset(payload) != _PAYLOAD_KEYS:
            raise _contract_invalid()
        content_hash = _required_text(payload["feed_content_hash"], max_chars=71)
        storage_ref = _required_text(payload["feed_storage_ref"], max_chars=82)
        try:
            expected_ref = canonical_storage_ref(content_hash)
        except ValueError as exc:
            raise _contract_invalid() from exc
        if storage_ref != expected_ref:
            raise _contract_invalid()
        feed_format = _required_text(payload["feed_format"], max_chars=16)
        if feed_format not in _ALLOWED_FORMATS:
            raise _contract_invalid()
        return cls(
            source_artifact_id=_uuid(payload["source_artifact_id"]),
            feed_content_hash=content_hash,
            feed_storage_ref=storage_ref,
            feed_format=feed_format,
            feed_title=_required_text(
                payload["feed_title"],
                max_chars=MAX_ITEM_TITLE_CHARS,
            ),
            item_id=_required_text(
                payload["item_id"],
                max_chars=MAX_ITEM_ID_CHARS,
            ),
            item_title=_required_text(
                payload["item_title"],
                max_chars=MAX_ITEM_TITLE_CHARS,
            ),
            item_url=_http_url(payload["item_url"]),
            published_at=_utc_timestamp(payload["published_at"]),
            summary_text=_optional_text(
                payload["summary_text"],
                max_chars=MAX_SUMMARY_CHARS,
            ),
        )


@dataclass(frozen=True, slots=True)
class FeedItemReviewRecord:
    queue_record: ProposalQueueRecord
    payload: FeedItemReviewPayload


@dataclass(frozen=True, slots=True)
class FeedItemReviewPage:
    items: tuple[FeedItemReviewRecord, ...]
    next_cursor: str | None


class SecuredFeedItemReviewService:
    def __init__(
        self,
        *,
        queue: SecuredProposalQueueService,
        knowledge: KnowledgeRepository,
    ) -> None:
        self._queue = queue
        self._knowledge = knowledge

    def list_feed_items(
        self,
        principal: AdminPrincipal,
        *,
        limit: int,
        cursor: str | None = None,
        review_state: ProposalQueueReviewState | None = None,
        run_id: UUID | None = None,
        now: datetime | None = None,
    ) -> FeedItemReviewPage:
        page: ProposalQueuePage = self._queue.list_queue(
            principal,
            limit=limit,
            cursor=cursor,
            review_state=review_state,
            proposal_kind=PROPOSAL_KIND,
            risk_code=RISK_CODE,
            run_id=run_id,
            pipeline_code=PIPELINE_CODE,
            now=now,
        )
        return FeedItemReviewPage(
            items=tuple(self._adapt(record) for record in page.items),
            next_cursor=page.next_cursor,
        )

    def detail(
        self,
        principal: AdminPrincipal,
        proposal_id: UUID,
        *,
        now: datetime | None = None,
    ) -> FeedItemReviewRecord:
        record = self._queue.detail(principal, proposal_id, now=now)
        if record.proposal.proposal_kind != PROPOSAL_KIND:
            raise DomainError(
                "ADMIN_FEED_ITEM_NOT_FOUND",
                "Feed item proposal not found",
                404,
            )
        return self._adapt(record)

    def _adapt(self, record: ProposalQueueRecord) -> FeedItemReviewRecord:
        proposal = record.proposal
        run = record.run
        if (
            proposal.proposal_kind != PROPOSAL_KIND
            or proposal.payload_schema_ref != PAYLOAD_SCHEMA_REF
            or proposal.payload_schema_version != PAYLOAD_SCHEMA_VERSION
            or proposal.risk_code != RISK_CODE
            or run.pipeline_code != PIPELINE_CODE
            or run.pipeline_version != PIPELINE_VERSION
            or run.input_artifact_kind is not InputArtifactKind.SOURCE_ARTIFACT
            or proposal.configuration_version != run.configuration_hash
        ):
            raise _contract_invalid()

        payload = FeedItemReviewPayload.from_mapping(proposal.payload)
        if (
            payload.source_artifact_id != run.input_artifact_id
            or payload.feed_content_hash != run.input_content_hash
            or proposal.provenance_ref != payload.feed_storage_ref
        ):
            raise _contract_invalid()

        artifact = self._knowledge.get_source_artifact(payload.source_artifact_id)
        if artifact is None:
            raise _contract_invalid()
        if (
            artifact.id != payload.source_artifact_id
            or artifact.content_hash != payload.feed_content_hash
            or artifact.raw_storage_ref != payload.feed_storage_ref
        ):
            raise _contract_invalid()
        return FeedItemReviewRecord(queue_record=record, payload=payload)


__all__ = [
    "FeedItemReviewPage",
    "FeedItemReviewPayload",
    "FeedItemReviewRecord",
    "SecuredFeedItemReviewService",
]
