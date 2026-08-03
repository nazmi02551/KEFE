from __future__ import annotations

from datetime import UTC, datetime

import pytest

from kefe_api.modules.knowledge.provider_http_capture import ProviderHttpCapturePlan
from kefe_api.modules.knowledge.provider_http_transport import (
    FinalProviderHttpError,
    OutboundHttpRequest,
    ProviderHttpMethod,
    ProviderHttpResponse,
    RetryableProviderHttpError,
)
from kefe_api.modules.knowledge.public_http_feed_capture import (
    PublicHttpFeedCaptureAdapter,
)
from kefe_api.modules.knowledge.rss_atom_parser import FeedParseLimits
from kefe_api.modules.knowledge.source_acquisition import (
    FinalSourceCaptureError,
    RetryableSourceCaptureError,
)
from kefe_api.modules.knowledge.source_evidence import (
    InMemoryRawSourceEvidenceStore,
    RetryableRawSourceEvidenceError,
)

NOW = datetime(2026, 8, 3, 4, 0, tzinfo=UTC)
ADAPTER_CODE = "test.public_feed.v1"
LOCATOR = "https://example.test/feed.xml"
RSS_BODY = (
    b"<rss version='2.0'><channel><title>Example</title>"
    b"<link>https://example.test/feed.xml</link>"
    b"<item><guid>one</guid><title>One</title></item>"
    b"</channel></rss>"
)


class Definition:
    adapter_code = ADAPTER_CODE
    parse_limits = FeedParseLimits()

    def build_plan(self, *, external_locator: str, trace_id: str, at: datetime):
        assert external_locator == LOCATOR
        assert trace_id == "trace-public-feed"
        assert at == NOW
        return ProviderHttpCapturePlan(
            adapter_code=self.adapter_code,
            request=OutboundHttpRequest(
                adapter_code=self.adapter_code,
                method=ProviderHttpMethod.GET,
                url=external_locator,
                public_headers=(("accept", "application/rss+xml"),),
            ),
        )


class MutableDefinition(Definition):
    def __init__(self) -> None:
        self.adapter_code = ADAPTER_CODE
        self.parse_limits = FeedParseLimits()


class Transport:
    def __init__(self, response=RSS_BODY, error: Exception | None = None) -> None:
        self.response = response
        self.error = error
        self.credential = object()
        self.calls = 0

    def execute(self, request, *, credential=None):
        self.calls += 1
        self.credential = credential
        if self.error is not None:
            raise self.error
        return ProviderHttpResponse(
            status_code=200,
            media_type="application/rss+xml",
            body=self.response,
            redirect_hops=0,
            elapsed_ms=5,
        )


class FailingStore:
    def __init__(self) -> None:
        self.calls = 0

    def seal(self, **kwargs):
        self.calls += 1
        del kwargs
        raise RetryableRawSourceEvidenceError("RAW_EVIDENCE_STORE_UNAVAILABLE")


def _adapter(*, transport=None, store=None, definition=None):
    return PublicHttpFeedCaptureAdapter(
        definition=definition or Definition(),
        transport=transport or Transport(),
        evidence_store=store or InMemoryRawSourceEvidenceStore(),
    )


def _capture(adapter):
    return adapter.capture(
        external_locator=LOCATOR,
        trace_id="trace-public-feed",
        at=NOW,
    )


def test_public_http_feed_capture_uses_no_credential_and_trusted_evidence() -> None:
    transport = Transport()
    store = InMemoryRawSourceEvidenceStore()
    captured = _capture(_adapter(transport=transport, store=store))

    assert transport.calls == 1
    assert transport.credential is None
    assert captured.external_id == LOCATOR
    assert captured.canonical_url == LOCATOR
    assert captured.content_hash.startswith("sha256:")
    assert captured.raw_storage_ref.startswith("evidence://sha256/")
    assert store.read_owned_copy(captured.raw_storage_ref) == RSS_BODY


def test_evidence_failure_precedes_feed_parsing_and_writes_no_artifact() -> None:
    transport = Transport(response=b"<not-valid")
    store = FailingStore()
    with pytest.raises(RetryableSourceCaptureError) as captured:
        _capture(_adapter(transport=transport, store=store))
    assert captured.value.code == "SOURCE_RAW_EVIDENCE_STORE_UNAVAILABLE"
    assert store.calls == 1


def test_strict_parser_rejects_malformed_or_unsupported_body_after_seal() -> None:
    store = InMemoryRawSourceEvidenceStore()
    with pytest.raises(FinalSourceCaptureError) as malformed:
        _capture(_adapter(transport=Transport(response=b"<rss>"), store=store))
    assert malformed.value.code == "SOURCE_FEED_XML_MALFORMED"
    assert store.object_count == 1

    with pytest.raises(FinalSourceCaptureError) as unsupported:
        _capture(_adapter(transport=Transport(response=b"<feed/>")))
    assert unsupported.value.code == "SOURCE_FEED_FORMAT_UNSUPPORTED"


def test_http_retryable_and_final_errors_preserve_bounded_codes() -> None:
    with pytest.raises(RetryableSourceCaptureError) as retryable:
        _capture(
            _adapter(
                transport=Transport(
                    error=RetryableProviderHttpError("PROVIDER_HTTP_TIMEOUT")
                )
            )
        )
    assert retryable.value.code == "SOURCE_PROVIDER_HTTP_TIMEOUT"

    with pytest.raises(FinalSourceCaptureError) as final:
        _capture(
            _adapter(
                transport=Transport(
                    error=FinalProviderHttpError("PROVIDER_HTTP_URL_NOT_ALLOWED")
                )
            )
        )
    assert final.value.code == "SOURCE_PROVIDER_HTTP_URL_NOT_ALLOWED"


def test_invalid_plan_mismatch_and_input_fail_closed() -> None:
    definition = MutableDefinition()
    adapter = _adapter(definition=definition)
    definition.adapter_code = "test.public_feed_other.v1"

    with pytest.raises(FinalSourceCaptureError) as mismatch:
        _capture(adapter)
    assert mismatch.value.code == "SOURCE_PUBLIC_HTTP_ADAPTER_MISMATCH"

    with pytest.raises(FinalSourceCaptureError) as invalid:
        _adapter().capture(
            external_locator=" padded ",
            trace_id="trace-public-feed",
            at=NOW,
        )
    assert invalid.value.code == "SOURCE_PUBLIC_HTTP_PLAN_INVALID"


def test_parse_limits_are_exact_and_snapshotted_at_construction() -> None:
    class InvalidDefinition(Definition):
        parse_limits = object()

    with pytest.raises(ValueError, match="exact FeedParseLimits"):
        _adapter(definition=InvalidDefinition())

    definition = MutableDefinition()
    definition.parse_limits = FeedParseLimits(max_text_chars=8192)
    adapter = _adapter(definition=definition)
    definition.parse_limits = FeedParseLimits(max_text_chars=1)
    captured = _capture(adapter)
    assert captured.content_hash.startswith("sha256:")
