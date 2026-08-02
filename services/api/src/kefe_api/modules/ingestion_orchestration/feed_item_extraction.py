from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit
from xml.etree import ElementTree

from kefe_api.modules.ingestion_orchestration.models import (
    ExecutorKind,
    IngestionRun,
    InputArtifactKind,
    ProposalDraft,
    StageProcessorResult,
)
from kefe_api.modules.ingestion_orchestration.service import (
    FinalStageError,
    RetryableStageError,
)
from kefe_api.modules.ingestion_orchestration.worker_runtime import (
    IngestionRuntimePlan,
    IngestionRuntimeStage,
    InMemoryIngestionWorkerRuntimeRegistry,
)
from kefe_api.modules.knowledge.ports import KnowledgeRepository
from kefe_api.modules.knowledge.provider_http_transport import ProviderHttpResponse
from kefe_api.modules.knowledge.provider_public_http_capture import (
    FinalPublicHttpParseError,
)
from kefe_api.modules.knowledge.rss_atom_capture import (
    ATOM_NAMESPACE,
    StrictRssAtomCaptureDefinition,
    StrictRssAtomParseProfile,
)
from kefe_api.modules.knowledge.source_evidence import (
    FinalRawSourceEvidenceError,
    RawSourceEvidenceRead,
    RawSourceEvidenceReader,
    RetryableRawSourceEvidenceError,
    canonical_storage_ref,
)

PIPELINE_CODE = "RSS_ATOM_FEED_ITEM_EXTRACTION"
PIPELINE_VERSION = "1.0.0"
STAGE_CODE = "EXTRACT_FEED_ITEMS"
STAGE_VERSION = "1.0.0"
PROPOSAL_KIND = "FEED_ITEM"
PAYLOAD_SCHEMA_REF = "kefe.feed-item"
PAYLOAD_SCHEMA_VERSION = "1.0.0"
RISK_CODE = "UNREVIEWED_EXTERNAL_FEED_ITEM"

MAX_ITEM_ID_CHARS = 4096
MAX_ITEM_TITLE_CHARS = 4096
MAX_ITEM_URL_CHARS = 4096
MAX_SUMMARY_CHARS = 16_384
MAX_PROPOSALS = 256
MAX_TOTAL_OUTPUT_CHARS = 524_288


def _fail(code: str) -> None:
    raise FinalStageError(code)


def _normalize_text(value: str) -> str:
    return " ".join(value.split())


def _tag_parts(tag: str) -> tuple[str | None, str]:
    if tag.startswith("{"):
        namespace, separator, local_name = tag[1:].partition("}")
        if not separator or not namespace or not local_name:
            _fail("FEED_ITEM_DOCUMENT_INVALID")
        return namespace, local_name
    return None, tag


def _bounded_text(
    value: str,
    *,
    max_chars: int,
    required: bool,
) -> str | None:
    normalized = _normalize_text(value)
    if not normalized:
        if required:
            _fail("FEED_ITEM_PAYLOAD_INVALID")
        return None
    if len(normalized) > max_chars:
        _fail("FEED_ITEM_OUTPUT_BUDGET_EXCEEDED")
    return normalized


def _validated_http_url(value: str) -> str:
    normalized = _bounded_text(
        value,
        max_chars=MAX_ITEM_URL_CHARS,
        required=True,
    )
    assert normalized is not None
    try:
        parsed = urlsplit(normalized)
        port = parsed.port
    except ValueError as exc:
        raise FinalStageError("FEED_ITEM_PAYLOAD_INVALID") from exc
    if parsed.scheme not in {"http", "https"}:
        _fail("FEED_ITEM_PAYLOAD_INVALID")
    if parsed.username is not None or parsed.password is not None:
        _fail("FEED_ITEM_PAYLOAD_INVALID")
    if parsed.hostname is None or parsed.fragment:
        _fail("FEED_ITEM_PAYLOAD_INVALID")
    if port not in (None, 80, 443):
        _fail("FEED_ITEM_PAYLOAD_INVALID")
    return normalized


def _rss_timestamp(value: str) -> datetime:
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise FinalStageError("FEED_ITEM_DOCUMENT_INVALID") from exc
    if parsed.tzinfo is None:
        _fail("FEED_ITEM_DOCUMENT_INVALID")
    return parsed.astimezone(UTC)


def _atom_timestamp(value: str) -> datetime:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise FinalStageError("FEED_ITEM_DOCUMENT_INVALID") from exc
    if parsed.tzinfo is None:
        _fail("FEED_ITEM_DOCUMENT_INVALID")
    return parsed.astimezone(UTC)


@dataclass(frozen=True, slots=True)
class ExtractedFeedItem:
    item_id: str
    title: str
    item_url: str | None
    published_at: datetime | None
    summary_text: str | None

    def __post_init__(self) -> None:
        if _bounded_text(
            self.item_id,
            max_chars=MAX_ITEM_ID_CHARS,
            required=True,
        ) != self.item_id:
            raise ValueError("item_id must be canonical bounded text")
        if _bounded_text(
            self.title,
            max_chars=MAX_ITEM_TITLE_CHARS,
            required=True,
        ) != self.title:
            raise ValueError("title must be canonical bounded text")
        if self.item_url is not None and _validated_http_url(self.item_url) != self.item_url:
            raise ValueError("item_url must be canonical")
        if self.published_at is not None:
            if (
                self.published_at.tzinfo is None
                or self.published_at.utcoffset() != UTC.utcoffset(self.published_at)
            ):
                raise ValueError("published_at must be timezone-aware UTC")
        if self.summary_text is not None and _bounded_text(
            self.summary_text,
            max_chars=MAX_SUMMARY_CHARS,
            required=False,
        ) != self.summary_text:
            raise ValueError("summary_text must be canonical bounded text")


@dataclass(frozen=True, slots=True)
class ExtractedFeedDocument:
    format_code: str
    feed_title: str
    items: tuple[ExtractedFeedItem, ...]

    def __post_init__(self) -> None:
        if self.format_code not in {"ATOM_1_0", "RSS_2_0"}:
            raise ValueError("format_code is invalid")
        if _bounded_text(
            self.feed_title,
            max_chars=MAX_ITEM_TITLE_CHARS,
            required=True,
        ) != self.feed_title:
            raise ValueError("feed_title must be canonical bounded text")
        if len(self.items) > MAX_PROPOSALS:
            raise ValueError("too many feed items")
        identities = tuple(item.item_id for item in self.items)
        if len(set(identities)) != len(identities):
            raise ValueError("duplicate feed item identity")


class FeedItemExtractionStageProcessor:
    def __init__(
        self,
        *,
        knowledge: KnowledgeRepository,
        evidence: RawSourceEvidenceReader,
        profile: StrictRssAtomParseProfile | None = None,
    ) -> None:
        resolved_profile = profile or StrictRssAtomParseProfile()
        if not isinstance(resolved_profile, StrictRssAtomParseProfile):
            raise ValueError("feed item extraction requires an exact parser profile")
        if resolved_profile.max_items > MAX_PROPOSALS:
            raise ValueError("parser item budget exceeds proposal budget")
        self._knowledge = knowledge
        self._evidence = evidence
        self._profile = resolved_profile

    def process(
        self,
        *,
        run: IngestionRun,
        stage_code: str,
        stage_version: str,
        input_hash: str,
    ) -> StageProcessorResult:
        if stage_code != STAGE_CODE or stage_version != STAGE_VERSION:
            _fail("FEED_ITEM_STAGE_IDENTITY_INVALID")
        if run.pipeline_code != PIPELINE_CODE or run.pipeline_version != PIPELINE_VERSION:
            _fail("FEED_ITEM_STAGE_IDENTITY_INVALID")
        if run.input_artifact_kind is not InputArtifactKind.SOURCE_ARTIFACT:
            _fail("FEED_ITEM_INPUT_KIND_INVALID")
        if input_hash != run.input_content_hash:
            _fail("FEED_ITEM_SOURCE_ARTIFACT_MISMATCH")

        artifact = self._knowledge.get_source_artifact(run.input_artifact_id)
        if artifact is None:
            _fail("FEED_ITEM_SOURCE_ARTIFACT_NOT_FOUND")
        if artifact.id != run.input_artifact_id or artifact.content_hash != input_hash:
            _fail("FEED_ITEM_SOURCE_ARTIFACT_MISMATCH")
        if artifact.raw_storage_ref is None:
            _fail("FEED_ITEM_EVIDENCE_REFERENCE_MISSING")
        try:
            if canonical_storage_ref(artifact.content_hash) != artifact.raw_storage_ref:
                _fail("FEED_ITEM_SOURCE_ARTIFACT_MISMATCH")
        except ValueError as exc:
            raise FinalStageError("FEED_ITEM_SOURCE_ARTIFACT_MISMATCH") from exc

        evidence = self._read_evidence(
            storage_ref=artifact.raw_storage_ref,
            content_hash=artifact.content_hash,
        )
        definition = StrictRssAtomCaptureDefinition(
            adapter_code=artifact.adapter_code,
            profile=self._profile,
        )
        try:
            plan = definition.build_plan(
                external_locator=artifact.external_locator,
                trace_id=f"feed-item:{run.id}",
                at=artifact.captured_at,
            )
            feed_metadata = definition.parse_response(
                plan=plan,
                response=ProviderHttpResponse(
                    status_code=200,
                    media_type=evidence.media_type,
                    body=evidence.body,
                    redirect_hops=0,
                    elapsed_ms=0,
                ),
                trace_id=f"feed-item:{run.id}",
                at=artifact.captured_at,
            )
        except (FinalPublicHttpParseError, ValueError) as exc:
            raise FinalStageError("FEED_ITEM_DOCUMENT_INVALID") from exc

        document = self._extract_validated_document(evidence)
        if document.feed_title != feed_metadata.publisher_or_issuer:
            _fail("FEED_ITEM_DOCUMENT_INVALID")

        proposals = tuple(
            ProposalDraft(
                proposal_kind=PROPOSAL_KIND,
                payload_schema_ref=PAYLOAD_SCHEMA_REF,
                payload_schema_version=PAYLOAD_SCHEMA_VERSION,
                payload=self._payload(
                    source_artifact_id=str(artifact.id),
                    feed_content_hash=artifact.content_hash,
                    feed_storage_ref=artifact.raw_storage_ref,
                    document=document,
                    item=item,
                ),
                configuration_version=run.configuration_hash,
                risk_code=RISK_CODE,
                provenance_ref=artifact.raw_storage_ref,
            )
            for item in sorted(document.items, key=lambda candidate: candidate.item_id)
        )
        return StageProcessorResult(
            proposals=proposals,
            output_metadata={
                "source_artifact_id": str(artifact.id),
                "feed_content_hash": artifact.content_hash,
                "feed_format": document.format_code,
                "proposal_count": len(proposals),
            },
        )

    def _read_evidence(
        self,
        *,
        storage_ref: str,
        content_hash: str,
    ) -> RawSourceEvidenceRead:
        try:
            evidence = self._evidence.read(
                storage_ref=storage_ref,
                expected_content_hash=content_hash,
            )
        except RetryableRawSourceEvidenceError as exc:
            raise RetryableStageError("FEED_ITEM_EVIDENCE_RETRYABLE") from exc
        except FinalRawSourceEvidenceError as exc:
            raise FinalStageError("FEED_ITEM_EVIDENCE_INVALID") from exc
        except Exception as exc:
            raise RetryableStageError("FEED_ITEM_EVIDENCE_RETRYABLE") from exc
        if type(evidence) is not RawSourceEvidenceRead:
            _fail("FEED_ITEM_EVIDENCE_INVALID")
        if (
            evidence.content_hash != content_hash
            or evidence.storage_ref != storage_ref
            or evidence.byte_length != len(evidence.body)
        ):
            _fail("FEED_ITEM_EVIDENCE_INVALID")
        if evidence.media_type is None:
            _fail("FEED_ITEM_EVIDENCE_INVALID")
        return evidence

    def _extract_validated_document(
        self,
        evidence: RawSourceEvidenceRead,
    ) -> ExtractedFeedDocument:
        try:
            root = ElementTree.fromstring(evidence.body)
        except ElementTree.ParseError as exc:
            raise FinalStageError("FEED_ITEM_DOCUMENT_INVALID") from exc
        namespace, local_name = _tag_parts(root.tag)
        if namespace is None and local_name == "rss":
            return self._extract_rss(root)
        if namespace == ATOM_NAMESPACE and local_name == "feed":
            return self._extract_atom(root)
        _fail("FEED_ITEM_DOCUMENT_INVALID")

    def _extract_rss(self, root: ElementTree.Element) -> ExtractedFeedDocument:
        channel = self._one_child(root, None, "channel", required=True)
        assert channel is not None
        feed_title = self._child_text(
            channel,
            None,
            "title",
            required=True,
            max_chars=MAX_ITEM_TITLE_CHARS,
        )
        assert feed_title is not None
        extracted: list[ExtractedFeedItem] = []
        identities: set[str] = set()
        for item in self._children(channel, None, "item"):
            title = self._child_text(
                item,
                None,
                "title",
                required=True,
                max_chars=MAX_ITEM_TITLE_CHARS,
            )
            guid = self._child_text(
                item,
                None,
                "guid",
                required=False,
                max_chars=MAX_ITEM_ID_CHARS,
            )
            link = self._child_text(
                item,
                None,
                "link",
                required=False,
                max_chars=MAX_ITEM_URL_CHARS,
            )
            validated_link = _validated_http_url(link) if link is not None else None
            identity = guid or validated_link
            if identity is None:
                _fail("FEED_ITEM_PAYLOAD_INVALID")
            if identity in identities:
                _fail("FEED_ITEM_DUPLICATE_IDENTITY")
            identities.add(identity)
            published = self._child_text(
                item,
                None,
                "pubDate",
                required=False,
                max_chars=256,
            )
            summary = self._child_text(
                item,
                None,
                "description",
                required=False,
                max_chars=MAX_SUMMARY_CHARS,
            )
            assert title is not None
            extracted.append(
                ExtractedFeedItem(
                    item_id=identity,
                    title=title,
                    item_url=validated_link,
                    published_at=(
                        _rss_timestamp(published)
                        if published is not None
                        else None
                    ),
                    summary_text=summary,
                )
            )
        return self._document("RSS_2_0", feed_title, extracted)

    def _extract_atom(self, root: ElementTree.Element) -> ExtractedFeedDocument:
        feed_title = self._child_text(
            root,
            ATOM_NAMESPACE,
            "title",
            required=True,
            max_chars=MAX_ITEM_TITLE_CHARS,
        )
        assert feed_title is not None
        extracted: list[ExtractedFeedItem] = []
        identities: set[str] = set()
        for entry in self._children(root, ATOM_NAMESPACE, "entry"):
            identity = self._child_text(
                entry,
                ATOM_NAMESPACE,
                "id",
                required=True,
                max_chars=MAX_ITEM_ID_CHARS,
            )
            title = self._child_text(
                entry,
                ATOM_NAMESPACE,
                "title",
                required=True,
                max_chars=MAX_ITEM_TITLE_CHARS,
            )
            updated = self._child_text(
                entry,
                ATOM_NAMESPACE,
                "updated",
                required=True,
                max_chars=256,
            )
            assert identity is not None and title is not None and updated is not None
            if identity in identities:
                _fail("FEED_ITEM_DUPLICATE_IDENTITY")
            identities.add(identity)
            link = self._atom_alternate_link(entry)
            summary = self._child_text(
                entry,
                ATOM_NAMESPACE,
                "summary",
                required=False,
                max_chars=MAX_SUMMARY_CHARS,
            )
            if summary is None:
                summary = self._child_text(
                    entry,
                    ATOM_NAMESPACE,
                    "content",
                    required=False,
                    max_chars=MAX_SUMMARY_CHARS,
                )
            extracted.append(
                ExtractedFeedItem(
                    item_id=identity,
                    title=title,
                    item_url=link,
                    published_at=_atom_timestamp(updated),
                    summary_text=summary,
                )
            )
        return self._document("ATOM_1_0", feed_title, extracted)

    def _document(
        self,
        format_code: str,
        feed_title: str,
        items: list[ExtractedFeedItem],
    ) -> ExtractedFeedDocument:
        if len(items) > MAX_PROPOSALS:
            _fail("FEED_ITEM_OUTPUT_BUDGET_EXCEEDED")
        total_chars = len(feed_title)
        for item in items:
            total_chars += len(item.item_id) + len(item.title)
            total_chars += len(item.item_url or "") + len(item.summary_text or "")
        if total_chars > MAX_TOTAL_OUTPUT_CHARS:
            _fail("FEED_ITEM_OUTPUT_BUDGET_EXCEEDED")
        return ExtractedFeedDocument(
            format_code=format_code,
            feed_title=feed_title,
            items=tuple(items),
        )

    def _payload(
        self,
        *,
        source_artifact_id: str,
        feed_content_hash: str,
        feed_storage_ref: str,
        document: ExtractedFeedDocument,
        item: ExtractedFeedItem,
    ) -> dict[str, object]:
        return {
            "source_artifact_id": source_artifact_id,
            "feed_content_hash": feed_content_hash,
            "feed_storage_ref": feed_storage_ref,
            "feed_format": document.format_code,
            "feed_title": document.feed_title,
            "item_id": item.item_id,
            "item_title": item.title,
            "item_url": item.item_url,
            "published_at": (
                item.published_at.isoformat()
                if item.published_at is not None
                else None
            ),
            "summary_text": item.summary_text,
        }

    def _children(
        self,
        parent: ElementTree.Element,
        namespace: str | None,
        local_name: str,
    ) -> tuple[ElementTree.Element, ...]:
        found: list[ElementTree.Element] = []
        for child in list(parent):
            child_namespace, child_local_name = _tag_parts(child.tag)
            if child_namespace == namespace and child_local_name == local_name:
                found.append(child)
        return tuple(found)

    def _one_child(
        self,
        parent: ElementTree.Element,
        namespace: str | None,
        local_name: str,
        *,
        required: bool,
    ) -> ElementTree.Element | None:
        children = self._children(parent, namespace, local_name)
        if len(children) > 1:
            _fail("FEED_ITEM_DOCUMENT_INVALID")
        if not children:
            if required:
                _fail("FEED_ITEM_DOCUMENT_INVALID")
            return None
        return children[0]

    def _child_text(
        self,
        parent: ElementTree.Element,
        namespace: str | None,
        local_name: str,
        *,
        required: bool,
        max_chars: int,
    ) -> str | None:
        child = self._one_child(
            parent,
            namespace,
            local_name,
            required=required,
        )
        if child is None:
            return None
        return _bounded_text(
            "".join(child.itertext()),
            max_chars=max_chars,
            required=required,
        )

    def _atom_alternate_link(self, entry: ElementTree.Element) -> str | None:
        found: list[str] = []
        for link in self._children(entry, ATOM_NAMESPACE, "link"):
            relation = link.attrib.get("rel", "alternate")
            if relation != "alternate":
                continue
            href = link.attrib.get("href")
            if href is None:
                _fail("FEED_ITEM_PAYLOAD_INVALID")
            found.append(_validated_http_url(href))
        if len(set(found)) > 1:
            _fail("FEED_ITEM_PAYLOAD_INVALID")
        return found[0] if found else None


def build_feed_item_extraction_runtime(
    processor: FeedItemExtractionStageProcessor,
) -> InMemoryIngestionWorkerRuntimeRegistry:
    plan = IngestionRuntimePlan(
        pipeline_code=PIPELINE_CODE,
        pipeline_version=PIPELINE_VERSION,
        stages=(
            IngestionRuntimeStage(
                stage_code=STAGE_CODE,
                stage_version=STAGE_VERSION,
                max_attempts=3,
                executor_kind=ExecutorKind.DETERMINISTIC,
            ),
        ),
    )
    key = (PIPELINE_CODE, PIPELINE_VERSION, STAGE_CODE, STAGE_VERSION)
    return InMemoryIngestionWorkerRuntimeRegistry(
        plans=(plan,),
        processors={key: processor},
    )


__all__ = [
    "ExtractedFeedDocument",
    "ExtractedFeedItem",
    "FeedItemExtractionStageProcessor",
    "MAX_PROPOSALS",
    "PAYLOAD_SCHEMA_REF",
    "PAYLOAD_SCHEMA_VERSION",
    "PIPELINE_CODE",
    "PIPELINE_VERSION",
    "PROPOSAL_KIND",
    "STAGE_CODE",
    "STAGE_VERSION",
    "build_feed_item_extraction_runtime",
]
