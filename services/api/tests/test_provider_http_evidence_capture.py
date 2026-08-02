from __future__ import annotations

import inspect
from dataclasses import fields
from datetime import UTC, datetime

import pytest

from kefe_api.modules.knowledge.provider_http_capture import ProviderHttpCapturePlan
from kefe_api.modules.knowledge.provider_http_evidence_capture import (
    EvidenceBackedProviderHttpCaptureAdapter,
    EvidenceBackedProviderHttpCaptureAdapterFactory,
    EvidenceBackedProviderHttpCaptureDefinition,
    ProviderHttpParsedSource,
)
from kefe_api.modules.knowledge.provider_http_transport import (
    FinalProviderHttpError,
    OutboundHttpRequest,
    ProviderHttpMethod,
    ProviderHttpResponse,
    RetryableProviderHttpError,
)
from kefe_api.modules.knowledge.provider_secret_execution import (
    InMemoryCredentialAwareSourceCaptureRegistry,
)
from kefe_api.modules.knowledge.source_acquisition import (
    FinalSourceCaptureError,
    RetryableSourceCaptureError,
)
from kefe_api.modules.knowledge.source_evidence import (
    FinalRawSourceEvidenceError,
    InMemoryRawSourceEvidenceStore,
    RawSourceEvidenceSeal,
    RetryableRawSourceEvidenceError,
    canonical_content_hash,
    canonical_storage_ref,
)

ADAPTER_CODE = "test.provider_http_evidence.v1"
OTHER_ADAPTER_CODE = "test.provider_http_evidence_other.v1"
AT = datetime(2026, 8, 2, 20, 30, tzinfo=UTC)
BODY = b'{"items":[1,2,3]}'


def _request(
    *,
    adapter_code: str = ADAPTER_CODE,
) -> OutboundHttpRequest:
    return OutboundHttpRequest(
        adapter_code=adapter_code,
        method=ProviderHttpMethod.GET,
        url="https://api.example.com/feed",
        public_headers=(("accept", "application/json"),),
    )


def _plan(
    *,
    adapter_code: str = ADAPTER_CODE,
) -> ProviderHttpCapturePlan:
    return ProviderHttpCapturePlan(
        adapter_code=adapter_code,
        request=_request(adapter_code=adapter_code),
    )


def _response() -> ProviderHttpResponse:
    return ProviderHttpResponse(
        status_code=200,
        media_type="application/json",
        body=BODY,
        redirect_hops=0,
        elapsed_ms=14,
    )


def _parsed() -> ProviderHttpParsedSource:
    return ProviderHttpParsedSource(
        external_id="source-1",
        canonical_url="https://api.example.com/items/1",
        publisher_or_issuer="Example Publisher",
        published_at=datetime(2026, 8, 2, 19, 0, tzinfo=UTC),
        language_code="en",
        jurisdiction_code="GLOBAL",
    )


class StaticSecretAccess:
    def __init__(self) -> None:
        self.material = bytearray(b"topsecret")
        self.use_calls = 0

    def use_bytes(self, callback, *, at: datetime):
        self.use_calls += 1
        view = memoryview(self.material).toreadonly()
        try:
            return callback(view)
        finally:
            view.release()


class FakeHttpExecutor:
    def __init__(self, outcome, events: list[str]) -> None:
        self.outcome = outcome
        self.events = events
        self.secrets: list[object] = []

    def execute(self, request, *, secret, at: datetime):
        del request, at
        self.events.append("execute")
        self.secrets.append(secret)
        if isinstance(self.outcome, BaseException):
            raise self.outcome
        return self.outcome


class RecordingEvidenceStore:
    def __init__(self, events: list[str], outcome=None) -> None:
        self.events = events
        self.outcome = outcome
        self.delegate = InMemoryRawSourceEvidenceStore()
        self.calls = []

    def seal(self, *, adapter_code, body, media_type, sealed_at):
        self.events.append("seal")
        self.calls.append((adapter_code, body, media_type, sealed_at))
        if isinstance(self.outcome, BaseException):
            raise self.outcome
        if self.outcome is not None:
            return self.outcome
        return self.delegate.seal(
            adapter_code=adapter_code,
            body=body,
            media_type=media_type,
            sealed_at=sealed_at,
        )


class FakeDefinition:
    def __init__(
        self,
        *,
        events: list[str],
        adapter_code: str = ADAPTER_CODE,
        plan_result=None,
        parse_result=None,
        build_error: BaseException | None = None,
        parse_error: BaseException | None = None,
    ) -> None:
        self.adapter_code = adapter_code
        self.events = events
        self.plan_result = (
            _plan(adapter_code=adapter_code)
            if plan_result is None
            else plan_result
        )
        self.parse_result = _parsed() if parse_result is None else parse_result
        self.build_error = build_error
        self.parse_error = parse_error
        self.parse_calls = []

    def build_plan(self, *, external_locator, trace_id, at):
        del external_locator, trace_id, at
        self.events.append("build")
        if self.build_error is not None:
            raise self.build_error
        return self.plan_result

    def parse_response(self, *, plan, response, trace_id, at):
        self.events.append("parse")
        self.parse_calls.append((plan, response, trace_id, at))
        if self.parse_error is not None:
            raise self.parse_error
        return self.parse_result


def _adapter(
    *,
    definition: FakeDefinition | None = None,
    http_outcome=None,
    store_outcome=None,
):
    events: list[str] = []
    resolved_definition = definition or FakeDefinition(events=events)
    executor = FakeHttpExecutor(
        _response() if http_outcome is None else http_outcome,
        events,
    )
    store = RecordingEvidenceStore(events, store_outcome)
    adapter = EvidenceBackedProviderHttpCaptureAdapter(
        definition=resolved_definition,
        http_executor=executor,
        evidence_store=store,
    )
    return adapter, resolved_definition, executor, store, events


def test_metadata_type_cannot_supply_hash_or_storage_reference() -> None:
    assert tuple(item.name for item in fields(ProviderHttpParsedSource)) == (
        "external_id",
        "canonical_url",
        "publisher_or_issuer",
        "published_at",
        "language_code",
        "jurisdiction_code",
    )
    rendered = str(
        inspect.signature(
            EvidenceBackedProviderHttpCaptureDefinition.parse_response
        )
    )
    assert "ProviderHttpParsedSource" in rendered
    assert "content_hash" not in rendered
    assert "raw_storage_ref" not in rendered


def test_capture_orders_build_execute_seal_parse_and_assembles_canonical_source() -> None:
    adapter, definition, executor, store, events = _adapter()
    secret = StaticSecretAccess()

    captured = adapter.capture(
        external_locator="provider://feed/world",
        trace_id="trace-001",
        secret=secret,
        at=AT,
    )

    expected_hash = canonical_content_hash(BODY)
    assert events == ["build", "execute", "seal", "parse"]
    assert secret.use_calls == 0
    assert executor.secrets == [secret]
    assert store.calls == [(ADAPTER_CODE, BODY, "application/json", AT)]
    assert definition.parse_calls == [(_plan(), _response(), "trace-001", AT)]
    assert captured.content_hash == expected_hash
    assert captured.raw_storage_ref == canonical_storage_ref(expected_hash)
    assert captured.external_id == "source-1"
    assert captured.publisher_or_issuer == "Example Publisher"


def test_raw_evidence_is_sealed_before_parser_failure() -> None:
    events: list[str] = []
    definition = FakeDefinition(
        events=events,
        parse_error=ValueError("private raw payload detail"),
    )
    adapter, _, _, store, resolved_events = _adapter(definition=definition)
    definition.events = resolved_events

    with pytest.raises(FinalSourceCaptureError) as caught:
        adapter.capture(
            external_locator="provider://feed/world",
            trace_id="trace-001",
            secret=StaticSecretAccess(),
            at=AT,
        )

    assert caught.value.code == "SOURCE_PROVIDER_HTTP_EVIDENCE_RESPONSE_INVALID"
    assert "private raw payload detail" not in str(caught.value)
    assert resolved_events == ["build", "execute", "seal", "parse"]
    assert store.delegate.object_count == 1


@pytest.mark.parametrize(
    ("store_error", "expected_type", "expected_code"),
    [
        (
            RetryableRawSourceEvidenceError(
                "RAW_EVIDENCE_STORE_UNAVAILABLE"
            ),
            RetryableSourceCaptureError,
            "SOURCE_RAW_EVIDENCE_STORE_UNAVAILABLE",
        ),
        (
            FinalRawSourceEvidenceError("RAW_EVIDENCE_DIGEST_COLLISION"),
            FinalSourceCaptureError,
            "SOURCE_RAW_EVIDENCE_STORE_FINAL",
        ),
        (
            RuntimeError("storage credential detail"),
            RetryableSourceCaptureError,
            "SOURCE_RAW_EVIDENCE_STORE_UNAVAILABLE",
        ),
    ],
)
def test_store_failures_are_bounded_and_parser_is_not_called(
    store_error: BaseException,
    expected_type: type[BaseException],
    expected_code: str,
) -> None:
    adapter, definition, _, _, _ = _adapter(store_outcome=store_error)

    with pytest.raises(expected_type) as caught:
        adapter.capture(
            external_locator="provider://feed/world",
            trace_id="trace-001",
            secret=StaticSecretAccess(),
            at=AT,
        )

    assert caught.value.code == expected_code
    assert "storage credential detail" not in str(caught.value)
    assert definition.parse_calls == []


def test_forged_or_non_seal_store_result_fails_before_parser() -> None:
    other_body = b'{"items":[9,9,9]}'
    other_hash = canonical_content_hash(other_body)
    forged = RawSourceEvidenceSeal(
        content_hash=other_hash,
        storage_ref=canonical_storage_ref(other_hash),
        byte_length=len(BODY),
        media_type="application/json",
        sealed_at=AT,
    )
    adapter, definition, _, _, _ = _adapter(store_outcome=forged)

    with pytest.raises(FinalSourceCaptureError) as forged_result:
        adapter.capture(
            external_locator="provider://feed/world",
            trace_id="trace-001",
            secret=StaticSecretAccess(),
            at=AT,
        )
    assert forged_result.value.code == "SOURCE_RAW_EVIDENCE_CONTRACT_INVALID"
    assert definition.parse_calls == []

    adapter, definition, _, _, _ = _adapter(store_outcome=object())
    with pytest.raises(FinalSourceCaptureError) as wrong_type:
        adapter.capture(
            external_locator="provider://feed/world",
            trace_id="trace-001",
            secret=StaticSecretAccess(),
            at=AT,
        )
    assert wrong_type.value.code == "SOURCE_RAW_EVIDENCE_CONTRACT_INVALID"
    assert definition.parse_calls == []


def test_http_classification_is_preserved_before_evidence_storage() -> None:
    adapter, definition, _, store, _ = _adapter(
        http_outcome=RetryableProviderHttpError("PROVIDER_HTTP_TIMEOUT")
    )
    with pytest.raises(RetryableSourceCaptureError) as retryable:
        adapter.capture(
            external_locator="provider://feed/world",
            trace_id="trace-001",
            secret=StaticSecretAccess(),
            at=AT,
        )
    assert retryable.value.code == "SOURCE_PROVIDER_HTTP_TIMEOUT"
    assert store.calls == []
    assert definition.parse_calls == []

    adapter, definition, _, store, _ = _adapter(
        http_outcome=FinalProviderHttpError("PROVIDER_HTTP_URL_NOT_ALLOWED")
    )
    with pytest.raises(FinalSourceCaptureError) as final:
        adapter.capture(
            external_locator="provider://feed/world",
            trace_id="trace-001",
            secret=StaticSecretAccess(),
            at=AT,
        )
    assert final.value.code == "SOURCE_PROVIDER_HTTP_URL_NOT_ALLOWED"
    assert store.calls == []
    assert definition.parse_calls == []


def test_non_metadata_parser_result_is_bounded_after_sealing() -> None:
    events: list[str] = []
    definition = FakeDefinition(events=events, parse_result=object())
    adapter, _, _, store, resolved_events = _adapter(definition=definition)
    definition.events = resolved_events

    with pytest.raises(FinalSourceCaptureError) as caught:
        adapter.capture(
            external_locator="provider://feed/world",
            trace_id="trace-001",
            secret=StaticSecretAccess(),
            at=AT,
        )

    assert caught.value.code == "SOURCE_PROVIDER_HTTP_EVIDENCE_RESPONSE_INVALID"
    assert store.delegate.object_count == 1
    assert resolved_events == ["build", "execute", "seal", "parse"]


def test_factory_builds_registry_compatible_evidence_backed_adapter() -> None:
    events: list[str] = []
    executor = FakeHttpExecutor(_response(), events)
    store = RecordingEvidenceStore(events)
    definition = FakeDefinition(events=events)
    factory = EvidenceBackedProviderHttpCaptureAdapterFactory(
        http_executor=executor,
        evidence_store=store,
    )

    adapter = factory.create(definition)
    registry = InMemoryCredentialAwareSourceCaptureRegistry((adapter,))

    assert isinstance(adapter, EvidenceBackedProviderHttpCaptureAdapter)
    assert registry.get(ADAPTER_CODE) is adapter


def test_evidence_capture_has_no_provider_specific_or_direct_network_runtime() -> None:
    module_source = inspect.getsource(
        __import__(
            "kefe_api.modules.knowledge.provider_http_evidence_capture",
            fromlist=["provider_http_evidence_capture"],
        )
    ).lower()

    for provider_name in (
        "twitter",
        "youtube",
        "facebook",
        "instagram",
        "tiktok",
        "reddit",
    ):
        assert provider_name not in module_source
    for fragment in (
        "socket.",
        "ssl.",
        "http.client",
        "requests.",
        "httpx.",
        "use_bytes(",
    ):
        assert fragment not in module_source
