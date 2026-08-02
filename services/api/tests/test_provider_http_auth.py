from __future__ import annotations

import pickle
from collections import deque
from datetime import UTC, datetime, timedelta

import pytest

from kefe_api.infrastructure.provider_http_runtime import PinnedTlsHttpBackend
from kefe_api.modules.knowledge.provider_http_auth import (
    InMemoryProviderHttpAuthRegistry,
    OwnedSensitiveHttpHeaders,
    ProviderHttpAuthProfile,
    ProviderHttpAuthScheme,
    SecureProviderHttpExecutor,
)
from kefe_api.modules.knowledge.provider_http_transport import (
    ControlledProviderHttpTransport,
    FinalProviderHttpError,
    InMemoryProviderAdoptionRegistry,
    InMemoryProviderHttpObserver,
    OutboundHttpRequest,
    PinnedOutboundHttpRequest,
    ProviderAdoptionProfile,
    ProviderHttpMethod,
    RawHttpResponse,
    RetryableProviderHttpError,
)
from kefe_api.modules.knowledge.provider_secret_execution import SecretLease

ADAPTER_CODE = "test.provider_auth.v1"
AT = datetime(2026, 8, 2, 19, 0, tzinfo=UTC)


def _adoption_profile(
    *,
    allowed_origins: tuple[str, ...] = ("https://api.example.com",),
    max_redirect_hops: int = 1,
) -> ProviderAdoptionProfile:
    return ProviderAdoptionProfile(
        adapter_code=ADAPTER_CODE,
        allowed_origins=allowed_origins,
        allowed_methods=(ProviderHttpMethod.GET,),
        allowed_media_types=("application/json",),
        connect_timeout_ms=100,
        read_timeout_ms=200,
        total_timeout_ms=1000,
        max_response_bytes=1024,
        max_redirect_hops=max_redirect_hops,
        terms_evidence_ref="docref://providers/example/terms-v1",
        rate_limit_evidence_ref="evidence://providers/example/rate-limit-v1",
    )


def _auth_profile(
    *,
    scheme: ProviderHttpAuthScheme = ProviderHttpAuthScheme.BEARER_AUTHORIZATION,
    credential_origin: str = "https://api.example.com",
    header_name: str = "authorization",
    max_secret_bytes: int = 128,
) -> ProviderHttpAuthProfile:
    return ProviderHttpAuthProfile(
        adapter_code=ADAPTER_CODE,
        scheme=scheme,
        credential_origin=credential_origin,
        header_name=header_name,
        max_secret_bytes=max_secret_bytes,
        auth_evidence_ref="evidence://providers/example/auth-v1",
    )


def _request(url: str = "https://api.example.com/feed") -> OutboundHttpRequest:
    return OutboundHttpRequest(
        adapter_code=ADAPTER_CODE,
        method=ProviderHttpMethod.GET,
        url=url,
        public_headers=(("accept", "application/json"),),
    )


def _response(
    status: int = 200,
    *,
    body: bytes = b"{}",
    location: str | None = None,
) -> RawHttpResponse:
    headers: list[tuple[str, str]] = []
    if status not in {204, 304} and not 300 <= status <= 399:
        headers.append(("content-type", "application/json"))
    if location is not None:
        headers.append(("location", location))
    return RawHttpResponse(
        status_code=status,
        headers=tuple(sorted(headers)),
        body=body,
        elapsed_ms=10,
    )


class FakeDnsResolver:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def resolve(self, host: str) -> tuple[str, ...]:
        self.calls.append(host)
        return ("8.8.8.8",)


class FakeBackend:
    def __init__(self, outcomes) -> None:
        self.outcomes = deque(outcomes)
        self.requests: list[PinnedOutboundHttpRequest] = []
        self.credentials: list[tuple[tuple[str, bytes], ...] | None] = []

    def execute(self, request: PinnedOutboundHttpRequest) -> RawHttpResponse:
        self.requests.append(request)
        if request.sensitive_headers is None:
            self.credentials.append(None)
        else:
            captured = request.sensitive_headers.use_headers(
                lambda entries: tuple((name, bytes(value)) for name, value in entries)
            )
            self.credentials.append(captured)
        outcome = self.outcomes.popleft()
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


def _executor(
    *,
    adoption_profile: ProviderAdoptionProfile | None = None,
    auth_profile: ProviderHttpAuthProfile | None = None,
    outcomes=None,
):
    resolver = FakeDnsResolver()
    backend = FakeBackend((_response(),) if outcomes is None else outcomes)
    observer = InMemoryProviderHttpObserver()
    transport = ControlledProviderHttpTransport(
        adoption_registry=InMemoryProviderAdoptionRegistry(
            () if adoption_profile is None else (adoption_profile,)
        ),
        dns_resolver=resolver,
        backend=backend,
        observer=observer,
        monotonic_clock=lambda: 0,
    )
    executor = SecureProviderHttpExecutor(
        auth_registry=InMemoryProviderHttpAuthRegistry(
            () if auth_profile is None else (auth_profile,)
        ),
        transport=transport,
    )
    return executor, resolver, backend, observer


class StaticSecretAccess:
    def __init__(self, material: bytes) -> None:
        self.material = bytearray(material)
        self.calls = 0

    def use_bytes(self, callback, *, at: datetime):
        assert at.tzinfo is UTC
        self.calls += 1
        view = memoryview(self.material).toreadonly()
        try:
            return callback(view)
        finally:
            view.release()


def test_auth_profiles_are_exact_immutable_and_deny_sensitive_routing_headers() -> None:
    bearer = _auth_profile()
    assert bearer.header_name == "authorization"

    header = _auth_profile(
        scheme=ProviderHttpAuthScheme.HEADER_TOKEN,
        header_name="x-api-key",
    )
    assert header.immutable_configuration[-2] == 128

    with pytest.raises(ValueError, match="authorization"):
        _auth_profile(header_name="x-api-key")
    with pytest.raises(ValueError, match="authorization"):
        _auth_profile(
            scheme=ProviderHttpAuthScheme.HEADER_TOKEN,
            header_name="authorization",
        )
    with pytest.raises(ValueError, match="forbidden"):
        _auth_profile(
            scheme=ProviderHttpAuthScheme.HEADER_TOKEN,
            header_name="host",
        )
    with pytest.raises(ValueError, match="canonical"):
        _auth_profile(credential_origin="https://API.example.com")
    with pytest.raises(ValueError, match="supported range"):
        _auth_profile(max_secret_bytes=0)


def test_auth_registry_rejects_duplicate_and_conflicting_profiles() -> None:
    profile = _auth_profile()
    with pytest.raises(ValueError, match="duplicate"):
        InMemoryProviderHttpAuthRegistry((profile, profile))

    conflict = _auth_profile(max_secret_bytes=64)
    with pytest.raises(ValueError, match="conflicting"):
        InMemoryProviderHttpAuthRegistry((profile, conflict))


def test_owned_sensitive_headers_are_redacted_scoped_and_zeroized() -> None:
    envelope = OwnedSensitiveHttpHeaders(
        (("authorization", bytearray(b"Bearer topsecret")),)
    )
    owned = envelope._entries[0][1]
    retained_view: list[memoryview] = []

    def inspect(entries: tuple[tuple[str, memoryview], ...]) -> bytes:
        assert entries[0][0] == "authorization"
        assert entries[0][1].readonly is True
        retained_view.append(entries[0][1])
        return bytes(entries[0][1])

    assert envelope.use_headers(inspect) == b"Bearer topsecret"
    with pytest.raises(ValueError):
        retained_view[0].tobytes()
    assert "topsecret" not in repr(envelope)
    with pytest.raises(TypeError):
        hash(envelope)
    with pytest.raises(TypeError):
        _ = envelope == envelope
    with pytest.raises(TypeError):
        pickle.dumps(envelope)

    envelope.close()
    envelope.close()
    assert envelope.closed is True
    assert owned == bytearray(len(owned))
    with pytest.raises(RuntimeError, match="CLOSED"):
        envelope.use_headers(lambda entries: entries)


def test_secure_executor_applies_bearer_header_and_closes_envelope() -> None:
    executor, resolver, backend, observer = _executor(
        adoption_profile=_adoption_profile(),
        auth_profile=_auth_profile(),
    )
    lease = SecretLease(b"topsecret", expires_at=AT + timedelta(minutes=5))

    response = executor.execute(_request(), secret=lease, at=AT)

    assert response.body == b"{}"
    assert resolver.calls == ["api.example.com"]
    assert backend.credentials == [(("authorization", b"Bearer topsecret"),)]
    assert backend.requests[0].sensitive_headers is not None
    assert backend.requests[0].sensitive_headers.closed is True
    assert "topsecret" not in repr(backend.requests[0])
    assert lease.closed is False
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
    assert not ({"credential", "secret", "authorization"} & set(operational))
    lease.close()


def test_header_token_scheme_has_no_implicit_prefix() -> None:
    executor, _, backend, _ = _executor(
        adoption_profile=_adoption_profile(),
        auth_profile=_auth_profile(
            scheme=ProviderHttpAuthScheme.HEADER_TOKEN,
            header_name="x-api-key",
        ),
    )
    lease = SecretLease(b"key-123", expires_at=AT + timedelta(minutes=5))

    executor.execute(_request(), secret=lease, at=AT)

    assert backend.credentials == [(("x-api-key", b"key-123"),)]
    lease.close()


def test_missing_auth_profile_fails_before_secret_dns_or_backend() -> None:
    executor, resolver, backend, _ = _executor(
        adoption_profile=_adoption_profile(),
        auth_profile=None,
    )
    secret = StaticSecretAccess(b"topsecret")

    with pytest.raises(FinalProviderHttpError) as caught:
        executor.execute(_request(), secret=secret, at=AT)

    assert caught.value.code == "PROVIDER_HTTP_AUTH_PROFILE_NOT_REGISTERED"
    assert secret.calls == 0
    assert resolver.calls == []
    assert backend.requests == []


@pytest.mark.parametrize(
    "material",
    [
        b"",
        b"contains space",
        b"line\nbreak",
        bytes((0x80,)),
        b"x" * 129,
    ],
)
def test_invalid_secret_material_is_final_and_never_reaches_backend(
    material: bytes,
) -> None:
    executor, resolver, backend, _ = _executor(
        adoption_profile=_adoption_profile(),
        auth_profile=_auth_profile(max_secret_bytes=128),
    )

    with pytest.raises(FinalProviderHttpError) as caught:
        executor.execute(_request(), secret=StaticSecretAccess(material), at=AT)

    assert caught.value.code == "PROVIDER_HTTP_AUTH_SECRET_INVALID"
    assert resolver.calls == []
    assert backend.requests == []


def test_expired_secret_lease_maps_to_bounded_final_error() -> None:
    executor, _, backend, _ = _executor(
        adoption_profile=_adoption_profile(),
        auth_profile=_auth_profile(),
    )
    lease = SecretLease(b"topsecret", expires_at=AT)

    with pytest.raises(FinalProviderHttpError) as caught:
        executor.execute(_request(), secret=lease, at=AT)

    assert caught.value.code == "PROVIDER_HTTP_AUTH_SECRET_UNAVAILABLE"
    assert "topsecret" not in repr(caught.value)
    assert backend.requests == []
    lease.close()


def test_transport_error_classification_survives_auth_executor() -> None:
    executor, _, _, _ = _executor(
        adoption_profile=_adoption_profile(),
        auth_profile=_auth_profile(),
        outcomes=(RetryableProviderHttpError("PROVIDER_HTTP_UNAVAILABLE"),),
    )
    lease = SecretLease(b"topsecret", expires_at=AT + timedelta(minutes=5))

    with pytest.raises(RetryableProviderHttpError) as caught:
        executor.execute(_request(), secret=lease, at=AT)

    assert caught.value.code == "PROVIDER_HTTP_UNAVAILABLE"
    lease.close()


def test_auth_origin_must_be_part_of_adoption_profile() -> None:
    executor, resolver, backend, _ = _executor(
        adoption_profile=_adoption_profile(),
        auth_profile=_auth_profile(credential_origin="https://cdn.example.com"),
    )
    lease = SecretLease(b"topsecret", expires_at=AT + timedelta(minutes=5))

    with pytest.raises(FinalProviderHttpError) as caught:
        executor.execute(_request(), secret=lease, at=AT)

    assert caught.value.code == "PROVIDER_HTTP_AUTH_ORIGIN_NOT_ALLOWED"
    assert resolver.calls == []
    assert backend.requests == []
    lease.close()


def test_same_origin_redirect_reuses_sensitive_access_within_budget() -> None:
    executor, resolver, backend, observer = _executor(
        adoption_profile=_adoption_profile(max_redirect_hops=1),
        auth_profile=_auth_profile(),
        outcomes=(
            _response(302, body=b"", location="/next"),
            _response(200, body=b'{"ok":true}'),
        ),
    )
    lease = SecretLease(b"topsecret", expires_at=AT + timedelta(minutes=5))

    response = executor.execute(_request(), secret=lease, at=AT)

    assert response.redirect_hops == 1
    assert resolver.calls == ["api.example.com", "api.example.com"]
    assert len(backend.requests) == 2
    assert backend.credentials == [
        (("authorization", b"Bearer topsecret"),),
        (("authorization", b"Bearer topsecret"),),
    ]
    assert observer.results[-1].redirect_hops == 1
    lease.close()


def test_cross_origin_redirect_is_blocked_before_second_dns_or_backend_call() -> None:
    executor, resolver, backend, observer = _executor(
        adoption_profile=_adoption_profile(
            allowed_origins=(
                "https://api.example.com",
                "https://cdn.example.com",
            ),
            max_redirect_hops=1,
        ),
        auth_profile=_auth_profile(),
        outcomes=(
            _response(
                302,
                body=b"",
                location="https://cdn.example.com/next",
            ),
        ),
    )
    lease = SecretLease(b"topsecret", expires_at=AT + timedelta(minutes=5))

    with pytest.raises(FinalProviderHttpError) as caught:
        executor.execute(_request(), secret=lease, at=AT)

    assert caught.value.code == "PROVIDER_HTTP_AUTH_REDIRECT_BLOCKED"
    assert resolver.calls == ["api.example.com"]
    assert len(backend.requests) == 1
    assert observer.results[-1].error_code == "PROVIDER_HTTP_AUTH_REDIRECT_BLOCKED"
    lease.close()


class FakeHeaders:
    def __init__(self, entries: tuple[tuple[str, str], ...]) -> None:
        self._entries = entries

    def get_all(self, name: str):
        values = [value for key, value in self._entries if key.lower() == name.lower()]
        return values or None


class FakeResponse:
    status = 200
    version = 11

    def __init__(self) -> None:
        self.headers = FakeHeaders(
            (
                ("content-length", "2"),
                ("content-type", "application/json"),
            )
        )

    def read(self, amount: int | None = None) -> bytes:
        assert amount == 1025
        return b"{}"


class TrackingSensitiveAccess:
    def __init__(
        self,
        *,
        name: str = "authorization",
        value: bytes = b"Bearer topsecret",
    ) -> None:
        self.name = name
        self.value = bytearray(value)
        self.active = False
        self.calls = 0

    def use_headers(self, callback):
        self.calls += 1
        self.active = True
        view = memoryview(self.value).toreadonly()
        try:
            return callback(((self.name, view),))
        finally:
            view.release()
            self.active = False


class TrackingConnection:
    def __init__(self, access: TrackingSensitiveAccess) -> None:
        self.access = access
        self.headers: list[tuple[str, str | bytes]] = []
        self.ended_while_active = False
        self.closed = False
        self.response_requested = False

    def putrequest(self, method, url, skip_host=False, skip_accept_encoding=False):
        assert method == "GET"
        assert url == "/feed"
        assert skip_host is True
        assert skip_accept_encoding is True

    def putheader(self, header: str, *values: str | bytes) -> None:
        if isinstance(values[0], bytes):
            assert self.access.active is True
        self.headers.append((header, values[0]))

    def endheaders(self) -> None:
        self.ended_while_active = self.access.active

    def getresponse(self):
        self.response_requested = True
        return FakeResponse()

    def close(self) -> None:
        self.closed = True


class TrackingConnectionFactory:
    def __init__(self, connection: TrackingConnection) -> None:
        self.connection = connection

    def create(self, request, context):
        del request, context
        return self.connection


def _pinned_request(access) -> PinnedOutboundHttpRequest:
    return PinnedOutboundHttpRequest(
        adapter_code=ADAPTER_CODE,
        method=ProviderHttpMethod.GET,
        host="api.example.com",
        port=443,
        target_ip="8.8.8.8",
        request_target="/feed",
        public_headers=(("accept", "application/json"),),
        connect_timeout_ms=100,
        read_timeout_ms=200,
        max_response_bytes=1024,
        sensitive_headers=access,
    )


def test_pinned_backend_sends_and_ends_sensitive_headers_inside_callback() -> None:
    access = TrackingSensitiveAccess()
    connection = TrackingConnection(access)
    backend = PinnedTlsHttpBackend(
        connection_factory=TrackingConnectionFactory(connection),
        monotonic_clock=lambda: 0,
    )

    result = backend.execute(_pinned_request(access))

    assert result.body == b"{}"
    assert access.calls == 1
    assert access.active is False
    assert connection.ended_while_active is True
    assert ("authorization", b"Bearer topsecret") in connection.headers
    assert connection.response_requested is True
    assert connection.closed is True


def test_pinned_backend_rejects_invalid_or_closed_sensitive_access() -> None:
    invalid = TrackingSensitiveAccess(name="host", value=b"topsecret")
    invalid_connection = TrackingConnection(invalid)
    invalid_backend = PinnedTlsHttpBackend(
        connection_factory=TrackingConnectionFactory(invalid_connection),
        monotonic_clock=lambda: 0,
    )
    with pytest.raises(FinalProviderHttpError) as invalid_error:
        invalid_backend.execute(_pinned_request(invalid))
    assert invalid_error.value.code == "PROVIDER_HTTP_AUTH_HEADERS_INVALID"
    assert invalid_connection.response_requested is False
    assert invalid_connection.closed is True

    closed = OwnedSensitiveHttpHeaders(
        (("authorization", bytearray(b"Bearer topsecret")),)
    )
    closed.close()
    closed_access = TrackingSensitiveAccess()
    closed_connection = TrackingConnection(closed_access)
    closed_backend = PinnedTlsHttpBackend(
        connection_factory=TrackingConnectionFactory(closed_connection),
        monotonic_clock=lambda: 0,
    )
    with pytest.raises(FinalProviderHttpError) as unavailable:
        closed_backend.execute(_pinned_request(closed))
    assert unavailable.value.code == "PROVIDER_HTTP_AUTH_HEADERS_UNAVAILABLE"
    assert closed_connection.response_requested is False
    assert closed_connection.closed is True
