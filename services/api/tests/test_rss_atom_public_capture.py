from __future__ import annotations

from datetime import UTC, datetime

import pytest

from kefe_api.modules.ingestion_orchestration.in_memory import (
    InMemoryIngestionOrchestrationRepository,
)
from kefe_api.modules.ingestion_orchestration.service import (
    IngestionOrchestrationService,
)
from kefe_api.modules.knowledge.in_memory import InMemoryKnowledgeRepository
from kefe_api.modules.knowledge.provider_control import ProviderCredentialMode
from kefe_api.modules.knowledge.provider_control_memory import (
    InMemorySourceProviderAdmissionRepository,
)
from kefe_api.modules.knowledge.provider_control_service import (
    SourceProviderAdmissionService,
)
from kefe_api.modules.knowledge.provider_http_capture import ProviderHttpCapturePlan
from kefe_api.modules.knowledge.provider_http_transport import (
    FinalProviderHttpError,
    ProviderHttpResponse,
)
from kefe_api.modules.knowledge.provider_public_execution import (
    CredentialModeRoutingProviderCaptureExecutor,
    InMemoryPublicSourceCaptureRegistry,
    PermitBoundPublicCaptureExecutor,
)
from kefe_api.modules.knowledge.provider_public_http_capture import (
    EvidenceBackedPublicHttpCaptureAdapter,
    EvidenceBackedPublicHttpCaptureAdapterFactory,
    FinalPublicHttpParseError,
)
from kefe_api.modules.knowledge.provider_secret_execution import (
    InMemoryCredentialAwareSourceCaptureRegistry,
    InMemorySecretResolverRegistry,
    SecureProviderCaptureExecutor,
)
from kefe_api.modules.knowledge.rss_atom_capture import (
    RSS_ATOM_ACCEPT_HEADER,
    RSS_ATOM_USER_AGENT,
    StrictRssAtomCaptureDefinition,
    StrictRssAtomParseProfile,
)
from kefe_api.modules.knowledge.source_acquisition import (
    FinalSourceCaptureError,
    InMemorySourceCaptureRegistry,
    NoOpSourceAcquisitionObserver,
    SourceAcquisitionCommand,
    SourceAcquisitionOutcome,
    SourceAcquisitionService,
)
from kefe_api.modules.knowledge.source_evidence import (
    InMemoryRawSourceEvidenceStore,
    RetryableRawSourceEvidenceError,
    canonical_content_hash,
    canonical_storage_ref,
)

NOW = datetime(2026, 8, 3, 1, 0, tzinfo=UTC)
ADAPTER_CODE = "test.public_feed.v1"
FEED_URL = "https://feeds.example.test/news.xml"

RSS_BODY = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Example News</title>
    <link>https://www.example.test/news</link>
    <description>Example feed snapshot</description>
    <language>en-US</language>
    <lastBuildDate>Sun, 03 Aug 2026 00:30:00 GMT</lastBuildDate>
    <item>
      <guid>item-1</guid>
      <title>First item</title>
      <link>https://www.example.test/news/first</link>
      <pubDate>Sun, 03 Aug 2026 00:20:00 GMT</pubDate>
    </item>
  </channel>
</rss>
"""

ATOM_BODY = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="tr-TR">
  <id>urn:example:feed</id>
  <title>Atom Example</title>
  <updated>2026-08-03T00:40:00Z</updated>
  <entry>
    <id>urn:example:item:1</id>
    <title>Atom item</title>
    <updated>2026-08-03T00:35:00+00:00</updated>
  </entry>
</feed>
"""


class StaticPublicTransport:
    def __init__(
        self,
        response: ProviderHttpResponse | None = None,
        error: Exception | None = None,
    ) -> None:
        self.response = response
        self.error = error
        self.calls = 0
        self.request = None

    def execute(self, request):
        self.calls += 1
        self.request = request
        if self.error is not None:
            raise self.error
        assert self.response is not None
        return self.response


class RecordingEvidenceStore(InMemoryRawSourceEvidenceStore):
    def __init__(self) -> None:
        super().__init__()
        self.sealed = False

    def seal(self, **kwargs):
        result = super().seal(**kwargs)
        self.sealed = True
        return result


class FailingEvidenceStore:
    def seal(self, **kwargs):
        del kwargs
        raise RetryableRawSourceEvidenceError("RAW_EVIDENCE_STORE_UNAVAILABLE")


class EvidenceOrderDefinition:
    def __init__(
        self,
        inner: StrictRssAtomCaptureDefinition,
        store: RecordingEvidenceStore,
    ) -> None:
        self.inner = inner
        self.store = store
        self.parse_calls = 0

    @property
    def adapter_code(self) -> str:
        return self.inner.adapter_code

    def build_plan(self, **kwargs) -> ProviderHttpCapturePlan:
        return self.inner.build_plan(**kwargs)

    def parse_response(self, **kwargs):
        assert self.store.sealed is True
        self.parse_calls += 1
        return self.inner.parse_response(**kwargs)


def _response(
    body: bytes,
    *,
    media_type: str = "application/rss+xml",
    status_code: int = 200,
) -> ProviderHttpResponse:
    return ProviderHttpResponse(
        status_code=status_code,
        media_type=media_type,
        body=body,
        redirect_hops=0,
        elapsed_ms=12,
    )


def _plan(definition: StrictRssAtomCaptureDefinition) -> ProviderHttpCapturePlan:
    return definition.build_plan(
        external_locator=FEED_URL,
        trace_id="trace-feed",
        at=NOW,
    )


def test_rss_capture_seals_before_parse_and_uses_trusted_evidence() -> None:
    store = RecordingEvidenceStore()
    inner = StrictRssAtomCaptureDefinition(adapter_code=ADAPTER_CODE)
    definition = EvidenceOrderDefinition(inner, store)
    transport = StaticPublicTransport(_response(RSS_BODY))
    adapter = EvidenceBackedPublicHttpCaptureAdapter(
        definition=definition,
        transport=transport,  # type: ignore[arg-type]
        evidence_store=store,
    )

    captured = adapter.capture(
        external_locator=FEED_URL,
        trace_id="trace-rss",
        at=NOW,
    )

    expected_hash = canonical_content_hash(RSS_BODY)
    assert captured.content_hash == expected_hash
    assert captured.raw_storage_ref == canonical_storage_ref(expected_hash)
    assert captured.external_id == FEED_URL
    assert captured.canonical_url == FEED_URL
    assert captured.publisher_or_issuer == "Example News"
    assert captured.published_at == datetime(2026, 8, 3, 0, 30, tzinfo=UTC)
    assert captured.language_code == "en-us"
    assert definition.parse_calls == 1
    assert transport.calls == 1
    assert transport.request.public_headers == (
        ("accept", RSS_ATOM_ACCEPT_HEADER),
        ("user-agent", RSS_ATOM_USER_AGENT),
    )


def test_atom_capture_returns_feed_level_metadata_only() -> None:
    store = RecordingEvidenceStore()
    definition = StrictRssAtomCaptureDefinition(adapter_code=ADAPTER_CODE)
    adapter = EvidenceBackedPublicHttpCaptureAdapter(
        definition=definition,
        transport=StaticPublicTransport(
            _response(ATOM_BODY, media_type="application/atom+xml")
        ),  # type: ignore[arg-type]
        evidence_store=store,
    )

    captured = adapter.capture(
        external_locator=FEED_URL,
        trace_id="trace-atom",
        at=NOW,
    )

    assert captured.external_id == "urn:example:feed"
    assert captured.canonical_url == FEED_URL
    assert captured.publisher_or_issuer == "Atom Example"
    assert captured.published_at == datetime(2026, 8, 3, 0, 40, tzinfo=UTC)
    assert captured.language_code == "tr-tr"
    assert store.object_count == 1


@pytest.mark.parametrize(
    ("body", "expected_code"),
    (
        (
            b"<!DOCTYPE rss [<!ENTITY xxe SYSTEM 'file:///etc/passwd'>]>"
            b"<rss version='2.0'><channel><title>&xxe;</title></channel></rss>",
            "SOURCE_PUBLIC_HTTP_PARSE_UNSAFE_XML",
        ),
        (
            b"<?xml version='1.0'?><?unsafe data?><rss version='2.0'/>",
            "SOURCE_PUBLIC_HTTP_PARSE_UNSAFE_XML",
        ),
        (
            b"<?xml version='1.0' encoding='ISO-8859-1'?><rss version='2.0'/>",
            "SOURCE_PUBLIC_HTTP_PARSE_UNSAFE_XML",
        ),
        (
            b"<rss version='2.0'><channel><title>broken</channel></rss>",
            "SOURCE_PUBLIC_HTTP_PARSE_XML_INVALID",
        ),
        (
            b"<root/>",
            "SOURCE_PUBLIC_HTTP_PARSE_ROOT_UNSUPPORTED",
        ),
    ),
)
def test_parser_rejects_unsafe_or_invalid_xml(
    body: bytes,
    expected_code: str,
) -> None:
    definition = StrictRssAtomCaptureDefinition(adapter_code=ADAPTER_CODE)
    with pytest.raises(FinalPublicHttpParseError) as error:
        definition.parse_response(
            plan=_plan(definition),
            response=_response(body),
            trace_id="trace-invalid",
            at=NOW,
        )
    assert error.value.code == expected_code


def test_parser_enforces_item_depth_text_and_document_budgets() -> None:
    two_items = RSS_BODY.replace(
        b"</channel>",
        b"<item><guid>item-2</guid><title>Second</title></item></channel>",
    )
    item_limited = StrictRssAtomCaptureDefinition(
        adapter_code=ADAPTER_CODE,
        profile=StrictRssAtomParseProfile(max_items=1),
    )
    with pytest.raises(FinalPublicHttpParseError) as item_error:
        item_limited.parse_response(
            plan=_plan(item_limited),
            response=_response(two_items),
            trace_id="trace-items",
            at=NOW,
        )
    assert item_error.value.code == "SOURCE_PUBLIC_HTTP_PARSE_PROFILE_EXCEEDED"

    depth_limited = StrictRssAtomCaptureDefinition(
        adapter_code=ADAPTER_CODE,
        profile=StrictRssAtomParseProfile(max_depth=2),
    )
    with pytest.raises(FinalPublicHttpParseError) as depth_error:
        depth_limited.parse_response(
            plan=_plan(depth_limited),
            response=_response(RSS_BODY),
            trace_id="trace-depth",
            at=NOW,
        )
    assert depth_error.value.code == "SOURCE_PUBLIC_HTTP_PARSE_PROFILE_EXCEEDED"

    text_limited = StrictRssAtomCaptureDefinition(
        adapter_code=ADAPTER_CODE,
        profile=StrictRssAtomParseProfile(max_node_text_chars=4),
    )
    with pytest.raises(FinalPublicHttpParseError) as text_error:
        text_limited.parse_response(
            plan=_plan(text_limited),
            response=_response(RSS_BODY),
            trace_id="trace-text",
            at=NOW,
        )
    assert text_error.value.code == "SOURCE_PUBLIC_HTTP_PARSE_PROFILE_EXCEEDED"

    document_limited = StrictRssAtomCaptureDefinition(
        adapter_code=ADAPTER_CODE,
        profile=StrictRssAtomParseProfile(max_document_bytes=64),
    )
    with pytest.raises(FinalPublicHttpParseError) as document_error:
        document_limited.parse_response(
            plan=_plan(document_limited),
            response=_response(RSS_BODY),
            trace_id="trace-document",
            at=NOW,
        )
    assert document_error.value.code == "SOURCE_PUBLIC_HTTP_PARSE_DOCUMENT_TOO_LARGE"


def test_parser_rejects_invalid_timestamp_media_type_and_required_fields() -> None:
    definition = StrictRssAtomCaptureDefinition(adapter_code=ADAPTER_CODE)
    invalid_date = RSS_BODY.replace(
        b"Sun, 03 Aug 2026 00:30:00 GMT",
        b"not-a-date",
    )
    with pytest.raises(FinalPublicHttpParseError) as date_error:
        definition.parse_response(
            plan=_plan(definition),
            response=_response(invalid_date),
            trace_id="trace-date",
            at=NOW,
        )
    assert date_error.value.code == "SOURCE_PUBLIC_HTTP_PARSE_TIMESTAMP_INVALID"

    with pytest.raises(FinalPublicHttpParseError) as media_error:
        definition.parse_response(
            plan=_plan(definition),
            response=_response(RSS_BODY, media_type="text/html"),
            trace_id="trace-media",
            at=NOW,
        )
    assert media_error.value.code == "SOURCE_PUBLIC_HTTP_PARSE_MEDIA_TYPE_UNSUPPORTED"

    missing_title = RSS_BODY.replace(
        b"<title>Example News</title>",
        b"",
        1,
    )
    with pytest.raises(FinalPublicHttpParseError) as field_error:
        definition.parse_response(
            plan=_plan(definition),
            response=_response(missing_title),
            trace_id="trace-field",
            at=NOW,
        )
    assert field_error.value.code == (
        "SOURCE_PUBLIC_HTTP_PARSE_REQUIRED_FIELD_MISSING"
    )


def test_transport_and_evidence_failures_stop_before_parse() -> None:
    definition = StrictRssAtomCaptureDefinition(adapter_code=ADAPTER_CODE)
    transport_failure = EvidenceBackedPublicHttpCaptureAdapter(
        definition=definition,
        transport=StaticPublicTransport(
            error=FinalProviderHttpError("PROVIDER_HTTP_URL_NOT_ALLOWED")
        ),  # type: ignore[arg-type]
        evidence_store=RecordingEvidenceStore(),
    )
    with pytest.raises(FinalSourceCaptureError) as transport_error:
        transport_failure.capture(
            external_locator=FEED_URL,
            trace_id="trace-transport",
            at=NOW,
        )
    assert transport_error.value.code == "SOURCE_PROVIDER_HTTP_URL_NOT_ALLOWED"

    evidence_failure = EvidenceBackedPublicHttpCaptureAdapter(
        definition=definition,
        transport=StaticPublicTransport(_response(RSS_BODY)),  # type: ignore[arg-type]
        evidence_store=FailingEvidenceStore(),  # type: ignore[arg-type]
    )
    with pytest.raises(Exception) as evidence_error:
        evidence_failure.capture(
            external_locator=FEED_URL,
            trace_id="trace-evidence",
            at=NOW,
        )
    assert getattr(evidence_error.value, "code", None) == (
        "SOURCE_RAW_EVIDENCE_STORE_UNAVAILABLE"
    )


def test_factory_builds_public_adapter_and_plan_rejects_unsafe_locator() -> None:
    definition = StrictRssAtomCaptureDefinition(adapter_code=ADAPTER_CODE)
    factory = EvidenceBackedPublicHttpCaptureAdapterFactory(
        transport=StaticPublicTransport(_response(RSS_BODY)),  # type: ignore[arg-type]
        evidence_store=RecordingEvidenceStore(),
    )
    adapter = factory.create(definition)
    assert adapter.adapter_code == ADAPTER_CODE
    with pytest.raises(FinalSourceCaptureError) as error:
        adapter.capture(
            external_locator="http://feeds.example.test/news.xml",
            trace_id="trace-http",
            at=NOW,
        )
    assert error.value.code == "SOURCE_PUBLIC_HTTP_PLAN_INVALID"


def test_public_permit_to_http_evidence_to_source_artifact_vertical_slice() -> None:
    provider_repository = InMemorySourceProviderAdmissionRepository()
    provider = SourceProviderAdmissionService(provider_repository, clock=lambda: NOW)
    provider.register(
        adapter_code=ADAPTER_CODE,
        credential_mode=ProviderCredentialMode.PUBLIC,
        secret_ref=None,
        quota_limit=10,
        quota_window_seconds=60,
        failure_threshold=3,
        circuit_open_seconds=30,
        permit_ttl_seconds=30,
        created_at=NOW,
    )
    evidence_store = RecordingEvidenceStore()
    feed_adapter = EvidenceBackedPublicHttpCaptureAdapter(
        definition=StrictRssAtomCaptureDefinition(adapter_code=ADAPTER_CODE),
        transport=StaticPublicTransport(_response(RSS_BODY)),  # type: ignore[arg-type]
        evidence_store=evidence_store,
    )
    public_executor = PermitBoundPublicCaptureExecutor(
        contexts=provider_repository,
        adapters=InMemoryPublicSourceCaptureRegistry((feed_adapter,)),
    )
    secure_executor = SecureProviderCaptureExecutor(
        contexts=provider_repository,
        resolvers=InMemorySecretResolverRegistry(),
        adapters=InMemoryCredentialAwareSourceCaptureRegistry(),
    )
    router = CredentialModeRoutingProviderCaptureExecutor(
        contexts=provider_repository,
        public_executor=public_executor,
        credentialed_executor=secure_executor,
    )
    knowledge = InMemoryKnowledgeRepository()
    ingestion_repository = InMemoryIngestionOrchestrationRepository()
    acquisition = SourceAcquisitionService(
        knowledge_repository=knowledge,
        ingestion_service=IngestionOrchestrationService(ingestion_repository),
        registry=InMemorySourceCaptureRegistry(),
        observer=NoOpSourceAcquisitionObserver(),
        admission=provider,
        capture_executor=router,
        clock=lambda: NOW,
    )

    result = acquisition.acquire(
        SourceAcquisitionCommand(
            adapter_code=ADAPTER_CODE,
            external_locator=FEED_URL,
            pipeline_code="RSS_ATOM_FEED_SNAPSHOT",
            pipeline_version="1.0.0",
            configuration_hash="sha256:rss-atom-config",
        ),
        trace_id="trace-vertical-feed",
    )

    assert result.outcome is SourceAcquisitionOutcome.ADMITTED
    assert evidence_store.object_count == 1
    artifact = knowledge.get_source_artifact(result.source_artifact_id)
    assert artifact is not None
    assert artifact.content_hash == canonical_content_hash(RSS_BODY)
    assert artifact.canonical_url == FEED_URL
    assert len(ingestion_repository._runs) == 1
    permit = next(iter(provider_repository._permits.values()))
    assert permit.state.value == "SUCCEEDED"
