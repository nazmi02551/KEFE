from __future__ import annotations

from collections import deque

import pytest

from kefe_api.modules.knowledge.provider_http_transport import (
    ControlledProviderHttpTransport,
    FinalProviderHttpError,
    InMemoryProviderAdoptionRegistry,
    InMemoryProviderHttpObserver,
    OutboundHttpRequest,
    ProviderAdoptionProfile,
    ProviderHttpMethod,
    ProviderHttpOutcome,
    RawHttpResponse,
    RetryableProviderHttpError,
    UnconfiguredPinnedHttpBackend,
    UnconfiguredProviderDnsResolver,
)

ADAPTER_CODE = "test.provider_http.v1"


def _profile(
    *,
    allowed_origins: tuple[str, ...] = ("https://api.example.com",),
    allowed_methods: tuple[ProviderHttpMethod, ...] = (
        ProviderHttpMethod.GET,
        ProviderHttpMethod.HEAD,
    ),
    allowed_media_types: tuple[str, ...] = (
        "application/json",
        "application/xml",
    ),
    max_response_bytes: int = 1024,
    max_redirect_hops: int = 1,
    total_timeout_ms: int = 1000,
) -> ProviderAdoptionProfile:
    return ProviderAdoptionProfile(
        adapter_code=ADAPTER_CODE,
        allowed_origins=allowed_origins,
        allowed_methods=allowed_methods,
        allowed_media_types=allowed_media_types,
        connect_timeout_ms=100,
        read_timeout_ms=200,
        total_timeout_ms=total_timeout_ms,
        max_response_bytes=max_response_bytes,
        max_redirect_hops=max_redirect_hops,
        terms_evidence_ref="docref://providers/example/terms-v1",
        rate_limit_evidence_ref="evidence://providers/example/rate-limit-v1",
    )


class FakeDnsResolver:
    def __init__(self, answers: dict[str, tuple[str, ...]]) -> None:
        self.answers = answers
        self.calls: list[str] = []

    def resolve(self, host: str) -> tuple[str, ...]:
        self.calls.append(host)
        return self.answers[host]


class FakeBackend:
    def __init__(self, outcomes) -> None:
        self.outcomes = deque(outcomes)
        self.requests = []

    def execute(self, request):
        self.requests.append(request)
        outcome = self.outcomes.popleft()
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


def _transport(
    *,
    profile: ProviderAdoptionProfile | None = None,
    answers: dict[str, tuple[str, ...]] | None = None,
    outcomes=(),
):
    observer = InMemoryProviderHttpObserver()
    resolver = FakeDnsResolver(
        answers or {"api.example.com": ("8.8.8.8",)}
    )
    backend = FakeBackend(outcomes)
    transport = ControlledProviderHttpTransport(
        adoption_registry=InMemoryProviderAdoptionRegistry(
            () if profile is None else (profile,)
        ),
        dns_resolver=resolver,
        backend=backend,
        observer=observer,
        monotonic_clock=lambda: 0,
    )
    return transport, resolver, backend, observer


def _request(
    url: str = "https://api.example.com/feed",
    *,
    method: ProviderHttpMethod = ProviderHttpMethod.GET,
) -> OutboundHttpRequest:
    return OutboundHttpRequest(
        adapter_code=ADAPTER_CODE,
        method=method,
        url=url,
        public_headers=(("accept", "application/json"),),
    )


def _response(
    status: int = 200,
    *,
    content_type: str | None = "application/json; charset=utf-8",
    body: bytes = b"{}",
    elapsed_ms: int = 10,
    location: str | None = None,
) -> RawHttpResponse:
    headers: list[tuple[str, str]] = []
    if content_type is not None:
        headers.append(("content-type", content_type))
    if location is not None:
        headers.append(("location", location))
    return RawHttpResponse(
        status_code=status,
        headers=tuple(sorted(headers)),
        body=body,
        elapsed_ms=elapsed_ms,
    )


def test_profile_requires_canonical_exact_https_origins_and_budgets() -> None:
    assert _profile().allowed_origins == ("https://api.example.com",)

    with pytest.raises(ValueError, match="https"):
        _profile(allowed_origins=("http://api.example.com",))
    with pytest.raises(ValueError, match="wildcards"):
        _profile(allowed_origins=("https://*.example.com",))
    with pytest.raises(ValueError, match="canonical"):
        _profile(
            allowed_origins=(
                "https://z.example.com",
                "https://a.example.com",
            )
        )
    with pytest.raises(ValueError, match="response byte budget"):
        _profile(max_response_bytes=0)


def test_adoption_registry_rejects_duplicate_and_conflicting_profiles() -> None:
    profile = _profile()
    with pytest.raises(ValueError, match="duplicate"):
        InMemoryProviderAdoptionRegistry((profile, profile))

    conflict = _profile(max_response_bytes=2048)
    with pytest.raises(ValueError, match="conflicting"):
        InMemoryProviderAdoptionRegistry((profile, conflict))


def test_request_repr_redacts_url_and_headers() -> None:
    request = _request("https://api.example.com/private/path?cursor=opaque")
    rendered = repr(request)

    assert "private/path" not in rendered
    assert "cursor" not in rendered
    assert "application/json" not in rendered
    assert "<redacted>" in rendered


def test_request_rejects_credential_bearing_or_unsorted_headers() -> None:
    with pytest.raises(ValueError, match="not allowed"):
        OutboundHttpRequest(
            adapter_code=ADAPTER_CODE,
            method=ProviderHttpMethod.GET,
            url="https://api.example.com/feed",
            public_headers=(("authorization", "Bearer secret"),),
        )
    with pytest.raises(ValueError, match="sorted"):
        OutboundHttpRequest(
            adapter_code=ADAPTER_CODE,
            method=ProviderHttpMethod.GET,
            url="https://api.example.com/feed",
            public_headers=(("user-agent", "kefe"), ("accept", "application/json")),
        )


@pytest.mark.parametrize(
    "url,error_code",
    [
        ("http://api.example.com/feed", "PROVIDER_HTTP_URL_NOT_ALLOWED"),
        ("https://user@api.example.com/feed", "PROVIDER_HTTP_URL_NOT_ALLOWED"),
        ("https://api.example.com:444/feed", "PROVIDER_HTTP_URL_NOT_ALLOWED"),
        ("https://other.example.com/feed", "PROVIDER_HTTP_URL_NOT_ALLOWED"),
        ("https://api.example.com/feed#part", "PROVIDER_HTTP_URL_NOT_ALLOWED"),
        (
            "https://api.example.com/feed?access-token=value",
            "PROVIDER_HTTP_CREDENTIAL_QUERY_FORBIDDEN",
        ),
    ],
)
def test_url_policy_fails_before_dns_or_backend(url: str, error_code: str) -> None:
    transport, resolver, backend, observer = _transport(profile=_profile())

    with pytest.raises(FinalProviderHttpError) as caught:
        transport.execute(_request(url))

    assert caught.value.code == error_code
    assert resolver.calls == []
    assert backend.requests == []
    assert observer.results[-1].error_code == error_code


@pytest.mark.parametrize(
    "address",
    [
        "127.0.0.1",
        "10.0.0.1",
        "169.254.1.1",
        "224.0.0.1",
        "240.0.0.1",
        "0.0.0.0",
        "192.0.2.1",
        "::1",
        "fc00::1",
        "fe80::1",
        "ff00::1",
        "2001:db8::1",
    ],
)
def test_non_public_dns_targets_are_rejected(address: str) -> None:
    transport, _, backend, observer = _transport(
        profile=_profile(),
        answers={"api.example.com": (address,)},
    )

    with pytest.raises(FinalProviderHttpError) as caught:
        transport.execute(_request())

    assert caught.value.code == "PROVIDER_HTTP_TARGET_NOT_PUBLIC"
    assert backend.requests == []
    assert observer.results[-1].response_bytes == 0


def test_mixed_public_and_private_dns_answers_fail_closed() -> None:
    transport, _, backend, _ = _transport(
        profile=_profile(),
        answers={"api.example.com": ("8.8.8.8", "10.0.0.1")},
    )

    with pytest.raises(FinalProviderHttpError) as caught:
        transport.execute(_request())

    assert caught.value.code == "PROVIDER_HTTP_TARGET_NOT_PUBLIC"
    assert backend.requests == []


def test_invalid_or_empty_dns_answers_are_bounded() -> None:
    transport, _, _, _ = _transport(
        profile=_profile(),
        answers={"api.example.com": ("not-an-ip",)},
    )
    with pytest.raises(FinalProviderHttpError) as invalid:
        transport.execute(_request())
    assert invalid.value.code == "PROVIDER_HTTP_DNS_INVALID"

    transport, _, _, _ = _transport(
        profile=_profile(),
        answers={"api.example.com": ()},
    )
    with pytest.raises(RetryableProviderHttpError) as empty:
        transport.execute(_request())
    assert empty.value.code == "PROVIDER_HTTP_DNS_UNAVAILABLE"


def test_public_address_selection_is_deterministic_and_pinned() -> None:
    transport, resolver, backend, observer = _transport(
        profile=_profile(),
        answers={"api.example.com": ("8.8.8.8", "1.1.1.1", "8.8.8.8")},
        outcomes=(_response(),),
    )

    result = transport.execute(_request())

    assert result.body == b"{}"
    assert resolver.calls == ["api.example.com"]
    pinned = backend.requests[0]
    assert pinned.host == "api.example.com"
    assert pinned.port == 443
    assert pinned.target_ip == "1.1.1.1"
    assert pinned.request_target == "/feed"
    assert "feed" not in repr(pinned)
    assert observer.results[-1].outcome is ProviderHttpOutcome.SUCCEEDED


def test_redirect_is_revalidated_resolved_and_repinned_per_hop() -> None:
    transport, resolver, backend, observer = _transport(
        profile=_profile(max_redirect_hops=1),
        outcomes=(
            _response(302, content_type=None, body=b"", location="/next"),
            _response(200, body=b'{"ok":true}'),
        ),
    )

    result = transport.execute(_request())

    assert result.redirect_hops == 1
    assert result.body == b'{"ok":true}'
    assert resolver.calls == ["api.example.com", "api.example.com"]
    assert [item.request_target for item in backend.requests] == ["/feed", "/next"]
    assert observer.results[-1].redirect_hops == 1


def test_redirect_to_unapproved_origin_or_over_budget_is_blocked() -> None:
    transport, _, backend, _ = _transport(
        profile=_profile(max_redirect_hops=1),
        outcomes=(
            _response(
                302,
                content_type=None,
                body=b"",
                location="https://other.example.com/next",
            ),
        ),
    )
    with pytest.raises(FinalProviderHttpError) as origin:
        transport.execute(_request())
    assert origin.value.code == "PROVIDER_HTTP_URL_NOT_ALLOWED"
    assert len(backend.requests) == 1

    transport, _, backend, _ = _transport(
        profile=_profile(max_redirect_hops=0),
        outcomes=(
            _response(302, content_type=None, body=b"", location="/next"),
        ),
    )
    with pytest.raises(FinalProviderHttpError) as budget:
        transport.execute(_request())
    assert budget.value.code == "PROVIDER_HTTP_REDIRECT_BLOCKED"
    assert len(backend.requests) == 1


@pytest.mark.parametrize("status", [408, 425, 429, 500, 502, 503, 504])
def test_retryable_status_mapping_is_bounded(status: int) -> None:
    transport, _, _, observer = _transport(
        profile=_profile(),
        outcomes=(_response(status, body=b""),),
    )

    with pytest.raises(RetryableProviderHttpError) as caught:
        transport.execute(_request())

    assert caught.value.code == "PROVIDER_HTTP_STATUS_RETRYABLE"
    assert observer.results[-1].status_code == status
    assert observer.results[-1].outcome is ProviderHttpOutcome.RETRYABLE_FAILURE


def test_final_status_media_type_body_size_and_total_budget_are_enforced() -> None:
    transport, _, _, _ = _transport(
        profile=_profile(),
        outcomes=(_response(404, body=b""),),
    )
    with pytest.raises(FinalProviderHttpError) as status:
        transport.execute(_request())
    assert status.value.code == "PROVIDER_HTTP_STATUS_FINAL"

    transport, _, _, _ = _transport(
        profile=_profile(),
        outcomes=(_response(content_type="text/html", body=b"x"),),
    )
    with pytest.raises(FinalProviderHttpError) as media:
        transport.execute(_request())
    assert media.value.code == "PROVIDER_HTTP_MEDIA_TYPE_NOT_ALLOWED"

    transport, _, _, _ = _transport(
        profile=_profile(max_response_bytes=2),
        outcomes=(_response(body=b"123"),),
    )
    with pytest.raises(FinalProviderHttpError) as size:
        transport.execute(_request())
    assert size.value.code == "PROVIDER_HTTP_RESPONSE_TOO_LARGE"

    transport, _, _, _ = _transport(
        profile=_profile(total_timeout_ms=200),
        outcomes=(_response(elapsed_ms=201),),
    )
    with pytest.raises(RetryableProviderHttpError) as budget:
        transport.execute(_request())
    assert budget.value.code == "PROVIDER_HTTP_TOTAL_BUDGET_EXCEEDED"


def test_get_body_requires_allowed_media_type_but_head_and_304_do_not() -> None:
    transport, _, _, _ = _transport(
        profile=_profile(),
        outcomes=(_response(content_type=None, body=b"payload"),),
    )
    with pytest.raises(FinalProviderHttpError) as missing:
        transport.execute(_request())
    assert missing.value.code == "PROVIDER_HTTP_MEDIA_TYPE_NOT_ALLOWED"

    transport, _, _, _ = _transport(
        profile=_profile(),
        outcomes=(_response(content_type=None, body=b""),),
    )
    head = transport.execute(_request(method=ProviderHttpMethod.HEAD))
    assert head.media_type is None

    transport, _, _, observer = _transport(
        profile=_profile(),
        outcomes=(_response(304, content_type=None, body=b""),),
    )
    not_modified = transport.execute(_request())
    assert not_modified.status_code == 304
    assert observer.results[-1].outcome is ProviderHttpOutcome.NOT_MODIFIED


def test_backend_timeout_unavailability_and_unconfigured_ports_are_bounded() -> None:
    transport, _, _, _ = _transport(
        profile=_profile(),
        outcomes=(TimeoutError("secret detail"),),
    )
    with pytest.raises(RetryableProviderHttpError) as timeout:
        transport.execute(_request())
    assert timeout.value.code == "PROVIDER_HTTP_TIMEOUT"
    assert "secret detail" not in repr(timeout.value)

    transport, _, _, _ = _transport(
        profile=_profile(),
        outcomes=(OSError("provider hostname detail"),),
    )
    with pytest.raises(RetryableProviderHttpError) as unavailable:
        transport.execute(_request())
    assert unavailable.value.code == "PROVIDER_HTTP_UNAVAILABLE"

    observer = InMemoryProviderHttpObserver()
    inert = ControlledProviderHttpTransport(
        adoption_registry=InMemoryProviderAdoptionRegistry((_profile(),)),
        dns_resolver=UnconfiguredProviderDnsResolver(),
        backend=UnconfiguredPinnedHttpBackend(),
        observer=observer,
        monotonic_clock=lambda: 0,
    )
    with pytest.raises(RetryableProviderHttpError) as dns:
        inert.execute(_request())
    assert dns.value.code == "PROVIDER_HTTP_DNS_UNAVAILABLE"
    assert observer.results[-1].error_code == "PROVIDER_HTTP_DNS_UNAVAILABLE"


def test_empty_production_style_registry_fails_before_dns() -> None:
    transport, resolver, backend, observer = _transport(profile=None)

    with pytest.raises(FinalProviderHttpError) as caught:
        transport.execute(_request())

    assert caught.value.code == "PROVIDER_HTTP_PROFILE_NOT_REGISTERED"
    assert resolver.calls == []
    assert backend.requests == []
    assert observer.results[-1].error_code == "PROVIDER_HTTP_PROFILE_NOT_REGISTERED"


def test_operational_result_is_exact_allowlist_and_contains_no_sensitive_fields() -> None:
    transport, _, _, observer = _transport(
        profile=_profile(),
        outcomes=(_response(body=b'{"ok":true}'),),
    )
    transport.execute(
        _request("https://api.example.com/private?cursor=opaque")
    )

    operational = observer.results[-1].as_operational_dict()
    assert set(operational) == {
        "outcome",
        "adapter_code",
        "method",
        "status_code",
        "redirect_hops",
        "response_bytes",
        "elapsed_ms",
        "error_code",
    }
    serialized = repr(operational)
    for forbidden in (
        "private",
        "cursor",
        "opaque",
        "content-type",
        "application/json",
        '{"ok":true}',
    ):
        assert forbidden not in serialized
