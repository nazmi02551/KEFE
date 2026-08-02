from __future__ import annotations

import inspect
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest

from kefe_api.modules.knowledge.provider_http_capture import (
    MAX_EXTERNAL_LOCATOR_CHARS,
    MAX_TRACE_ID_CHARS,
    ProviderHttpCaptureAdapter,
    ProviderHttpCaptureAdapterFactory,
    ProviderHttpCaptureDefinition,
    ProviderHttpCapturePlan,
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
    CapturedSource,
    FinalSourceCaptureError,
    RetryableSourceCaptureError,
)

ADAPTER_CODE = "test.provider_http_capture.v1"
OTHER_ADAPTER_CODE = "test.provider_http_other.v1"
AT = datetime(2026, 8, 2, 19, 45, tzinfo=UTC)


def _request(
    *,
    adapter_code: str = ADAPTER_CODE,
    url: str = "https://api.example.com/feed",
) -> OutboundHttpRequest:
    return OutboundHttpRequest(
        adapter_code=adapter_code,
        method=ProviderHttpMethod.GET,
        url=url,
        public_headers=(("accept", "application/json"),),
    )


def _plan(*, adapter_code: str = ADAPTER_CODE) -> ProviderHttpCapturePlan:
    return ProviderHttpCapturePlan(
        adapter_code=adapter_code,
        request=_request(adapter_code=adapter_code),
    )


def _response() -> ProviderHttpResponse:
    return ProviderHttpResponse(
        status_code=200,
        media_type="application/json",
        body=b'{"items":[]}',
        redirect_hops=0,
        elapsed_ms=12,
    )


def _captured() -> CapturedSource:
    return CapturedSource(
        content_hash="sha256:0123456789abcdef",
        external_id="source-1",
        canonical_url="https://api.example.com/items/1",
        publisher_or_issuer="Example Publisher",
        language_code="en",
        jurisdiction_code="GLOBAL",
        raw_storage_ref="evidence://raw/example/source-1",
    )


class StaticSecretAccess:
    def __init__(self, material: bytes = b"topsecret") -> None:
        self.material = bytearray(material)
        self.use_calls = 0

    def use_bytes(self, callback, *, at: datetime):
        self.use_calls += 1
        view = memoryview(self.material).toreadonly()
        try:
            return callback(view)
        finally:
            view.release()


class FakeHttpExecutor:
    def __init__(self, outcome, events: list[str] | None = None) -> None:
        self.outcome = outcome
        self.events = events if events is not None else []
        self.requests: list[OutboundHttpRequest] = []
        self.secrets: list[object] = []
        self.times: list[datetime] = []

    def execute(
        self,
        request: OutboundHttpRequest,
        *,
        secret,
        at: datetime,
    ):
        self.events.append("execute")
        self.requests.append(request)
        self.secrets.append(secret)
        self.times.append(at)
        if isinstance(self.outcome, BaseException):
            raise self.outcome
        return self.outcome


class FakeDefinition:
    def __init__(
        self,
        *,
        adapter_code: str = ADAPTER_CODE,
        plan_result=None,
        parse_result=None,
        build_error: BaseException | None = None,
        parse_error: BaseException | None = None,
        events: list[str] | None = None,
    ) -> None:
        self.adapter_code = adapter_code
        self.plan_result = _plan(adapter_code=adapter_code) if plan_result is None else plan_result
        self.parse_result = _captured() if parse_result is None else parse_result
        self.build_error = build_error
        self.parse_error = parse_error
        self.events = events if events is not None else []
        self.build_calls: list[tuple[str, str, datetime]] = []
        self.parse_calls: list[
            tuple[ProviderHttpCapturePlan, ProviderHttpResponse, str, datetime]
        ] = []

    def build_plan(
        self,
        *,
        external_locator: str,
        trace_id: str,
        at: datetime,
    ):
        self.events.append("build")
        self.build_calls.append((external_locator, trace_id, at))
        if self.build_error is not None:
            raise self.build_error
        return self.plan_result

    def parse_response(
        self,
        *,
        plan: ProviderHttpCapturePlan,
        response: ProviderHttpResponse,
        trace_id: str,
        at: datetime,
    ):
        self.events.append("parse")
        self.parse_calls.append((plan, response, trace_id, at))
        if self.parse_error is not None:
            raise self.parse_error
        return self.parse_result


def _adapter(
    *,
    definition: FakeDefinition | None = None,
    outcome=None,
    events: list[str] | None = None,
):
    shared_events = events if events is not None else []
    resolved_definition = definition or FakeDefinition(events=shared_events)
    executor = FakeHttpExecutor(
        _response() if outcome is None else outcome,
        events=shared_events,
    )
    adapter = ProviderHttpCaptureAdapter(
        definition=resolved_definition,
        http_executor=executor,
    )
    return adapter, resolved_definition, executor


def test_plan_is_immutable_redacted_and_requires_exact_request_adapter() -> None:
    plan = _plan()

    assert plan.adapter_code == ADAPTER_CODE
    assert "api.example.com/feed" not in repr(plan)
    assert "application/json" not in repr(plan)
    assert "<redacted>" in repr(plan)
    with pytest.raises(FrozenInstanceError):
        plan.adapter_code = OTHER_ADAPTER_CODE  # type: ignore[misc]

    with pytest.raises(ValueError, match="adapter code mismatch"):
        ProviderHttpCapturePlan(
            adapter_code=ADAPTER_CODE,
            request=_request(adapter_code=OTHER_ADAPTER_CODE),
        )
    with pytest.raises(ValueError, match="OutboundHttpRequest"):
        ProviderHttpCapturePlan(
            adapter_code=ADAPTER_CODE,
            request=object(),  # type: ignore[arg-type]
        )


def test_definition_protocol_exposes_only_plan_and_bounded_parse_ports() -> None:
    build_parameters = tuple(
        inspect.signature(ProviderHttpCaptureDefinition.build_plan).parameters
    )
    parse_parameters = tuple(
        inspect.signature(ProviderHttpCaptureDefinition.parse_response).parameters
    )

    assert build_parameters == ("self", "external_locator", "trace_id", "at")
    assert parse_parameters == ("self", "plan", "response", "trace_id", "at")
    rendered = (
        str(inspect.signature(ProviderHttpCaptureDefinition.build_plan))
        + str(inspect.signature(ProviderHttpCaptureDefinition.parse_response))
    )
    for forbidden in (
        "SecretAccess",
        "SecretLease",
        "SensitiveHttpHeaderAccess",
        "ProviderDnsResolver",
        "PinnedHttpBackend",
        "socket",
        "SSLContext",
    ):
        assert forbidden not in rendered


def test_capture_orders_plan_execute_parse_and_wrapper_never_reads_secret() -> None:
    events: list[str] = []
    adapter, definition, executor = _adapter(events=events)
    secret = StaticSecretAccess()

    captured = adapter.capture(
        external_locator="provider://feed/world",
        trace_id="trace-001",
        secret=secret,
        at=AT,
    )

    assert captured == _captured()
    assert events == ["build", "execute", "parse"]
    assert secret.use_calls == 0
    assert executor.secrets == [secret]
    assert executor.requests == [_request()]
    assert executor.times == [AT]
    assert definition.build_calls == [("provider://feed/world", "trace-001", AT)]
    assert definition.parse_calls == [(_plan(), _response(), "trace-001", AT)]


@pytest.mark.parametrize(
    ("external_locator", "trace_id", "at"),
    [
        ("", "trace-001", AT),
        (" padded ", "trace-001", AT),
        ("x" * (MAX_EXTERNAL_LOCATOR_CHARS + 1), "trace-001", AT),
        ("provider://feed", "", AT),
        ("provider://feed", " padded ", AT),
        ("provider://feed", "x" * (MAX_TRACE_ID_CHARS + 1), AT),
        ("provider://feed", "trace-001", datetime(2026, 8, 2, 19, 45)),
    ],
)
def test_invalid_inputs_are_bounded_before_plan_or_execution(
    external_locator: str,
    trace_id: str,
    at: datetime,
) -> None:
    adapter, definition, executor = _adapter()
    secret = StaticSecretAccess()

    with pytest.raises(FinalSourceCaptureError) as caught:
        adapter.capture(
            external_locator=external_locator,
            trace_id=trace_id,
            secret=secret,
            at=at,
        )

    assert caught.value.code == "SOURCE_PROVIDER_HTTP_PLAN_INVALID"
    assert definition.build_calls == []
    assert executor.requests == []
    assert secret.use_calls == 0


def test_planning_failure_and_wrong_plan_type_are_bounded_before_execution() -> None:
    definition = FakeDefinition(build_error=RuntimeError("private locator detail"))
    adapter, _, executor = _adapter(definition=definition)

    with pytest.raises(FinalSourceCaptureError) as failed:
        adapter.capture(
            external_locator="provider://feed",
            trace_id="trace-001",
            secret=StaticSecretAccess(),
            at=AT,
        )
    assert failed.value.code == "SOURCE_PROVIDER_HTTP_PLAN_INVALID"
    assert "private locator detail" not in str(failed.value)
    assert executor.requests == []

    definition = FakeDefinition(plan_result=object())
    adapter, _, executor = _adapter(definition=definition)
    with pytest.raises(FinalSourceCaptureError) as wrong_type:
        adapter.capture(
            external_locator="provider://feed",
            trace_id="trace-001",
            secret=StaticSecretAccess(),
            at=AT,
        )
    assert wrong_type.value.code == "SOURCE_PROVIDER_HTTP_PLAN_INVALID"
    assert executor.requests == []


def test_definition_plan_adapter_drift_fails_closed_before_execution() -> None:
    definition = FakeDefinition(
        adapter_code=ADAPTER_CODE,
        plan_result=_plan(adapter_code=OTHER_ADAPTER_CODE),
    )
    adapter, _, executor = _adapter(definition=definition)

    with pytest.raises(FinalSourceCaptureError) as caught:
        adapter.capture(
            external_locator="provider://feed",
            trace_id="trace-001",
            secret=StaticSecretAccess(),
            at=AT,
        )

    assert caught.value.code == "SOURCE_PROVIDER_HTTP_ADAPTER_MISMATCH"
    assert executor.requests == []


def test_adapter_code_is_snapshotted_against_mutable_definition_drift() -> None:
    definition = FakeDefinition()
    adapter, _, _ = _adapter(definition=definition)

    definition.adapter_code = OTHER_ADAPTER_CODE

    assert adapter.adapter_code == ADAPTER_CODE


@pytest.mark.parametrize(
    ("error", "expected_type", "expected_code"),
    [
        (
            RetryableProviderHttpError("PROVIDER_HTTP_TIMEOUT"),
            RetryableSourceCaptureError,
            "SOURCE_PROVIDER_HTTP_TIMEOUT",
        ),
        (
            RetryableProviderHttpError("PROVIDER_HTTP_DNS_UNAVAILABLE"),
            RetryableSourceCaptureError,
            "SOURCE_PROVIDER_HTTP_DNS_UNAVAILABLE",
        ),
        (
            FinalProviderHttpError("PROVIDER_HTTP_AUTH_PROFILE_NOT_REGISTERED"),
            FinalSourceCaptureError,
            "SOURCE_PROVIDER_HTTP_AUTH_PROFILE_NOT_REGISTERED",
        ),
        (
            FinalProviderHttpError("PROVIDER_HTTP_URL_NOT_ALLOWED"),
            FinalSourceCaptureError,
            "SOURCE_PROVIDER_HTTP_URL_NOT_ALLOWED",
        ),
    ],
)
def test_http_error_classification_and_bounded_code_are_preserved(
    error: BaseException,
    expected_type: type[BaseException],
    expected_code: str,
) -> None:
    adapter, definition, _ = _adapter(outcome=error)

    with pytest.raises(expected_type) as caught:
        adapter.capture(
            external_locator="provider://feed",
            trace_id="trace-001",
            secret=StaticSecretAccess(),
            at=AT,
        )

    assert caught.value.code == expected_code
    assert definition.parse_calls == []


def test_invalid_provider_error_code_and_unexpected_execution_are_final_bounded() -> None:
    adapter, definition, _ = _adapter(
        outcome=RetryableProviderHttpError("provider detail with spaces")
    )
    with pytest.raises(FinalSourceCaptureError) as invalid_code:
        adapter.capture(
            external_locator="provider://feed",
            trace_id="trace-001",
            secret=StaticSecretAccess(),
            at=AT,
        )
    assert invalid_code.value.code == "SOURCE_PROVIDER_HTTP_EXECUTION_INVALID"
    assert definition.parse_calls == []

    adapter, definition, _ = _adapter(
        outcome=RuntimeError("socket and credential detail")
    )
    with pytest.raises(FinalSourceCaptureError) as unexpected:
        adapter.capture(
            external_locator="provider://feed",
            trace_id="trace-001",
            secret=StaticSecretAccess(),
            at=AT,
        )
    assert unexpected.value.code == "SOURCE_PROVIDER_HTTP_EXECUTION_INVALID"
    assert "socket and credential detail" not in str(unexpected.value)
    assert definition.parse_calls == []


def test_non_response_executor_result_is_rejected_before_parser() -> None:
    adapter, definition, _ = _adapter(outcome=object())

    with pytest.raises(FinalSourceCaptureError) as caught:
        adapter.capture(
            external_locator="provider://feed",
            trace_id="trace-001",
            secret=StaticSecretAccess(),
            at=AT,
        )

    assert caught.value.code == "SOURCE_PROVIDER_HTTP_EXECUTION_INVALID"
    assert definition.parse_calls == []


def test_parser_failure_and_non_exact_captured_source_are_final_bounded() -> None:
    definition = FakeDefinition(parse_error=ValueError("raw response body detail"))
    adapter, _, _ = _adapter(definition=definition)

    with pytest.raises(FinalSourceCaptureError) as failed:
        adapter.capture(
            external_locator="provider://feed",
            trace_id="trace-001",
            secret=StaticSecretAccess(),
            at=AT,
        )
    assert failed.value.code == "SOURCE_PROVIDER_HTTP_RESPONSE_INVALID"
    assert "raw response body detail" not in str(failed.value)

    definition = FakeDefinition(parse_result=object())
    adapter, _, _ = _adapter(definition=definition)
    with pytest.raises(FinalSourceCaptureError) as wrong_type:
        adapter.capture(
            external_locator="provider://feed",
            trace_id="trace-001",
            secret=StaticSecretAccess(),
            at=AT,
        )
    assert wrong_type.value.code == "SOURCE_PROVIDER_HTTP_RESPONSE_INVALID"


def test_factory_builds_structural_credential_adapter_for_existing_registry() -> None:
    executor = FakeHttpExecutor(_response())
    definition = FakeDefinition()
    factory = ProviderHttpCaptureAdapterFactory(executor)

    adapter = factory.create(definition)
    registry = InMemoryCredentialAwareSourceCaptureRegistry((adapter,))

    assert isinstance(adapter, ProviderHttpCaptureAdapter)
    assert adapter.adapter_code == ADAPTER_CODE
    assert registry.get(ADAPTER_CODE) is adapter


def test_no_provider_specific_runtime_or_live_network_dependency_is_present() -> None:
    module_source = inspect.getsource(
        __import__(
            "kefe_api.modules.knowledge.provider_http_capture",
            fromlist=["provider_http_capture"],
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
    for network_fragment in (
        "socket.",
        "ssl.",
        "http.client",
        "requests.",
        "httpx.",
        "urllib.request",
    ):
        assert network_fragment not in module_source
