from __future__ import annotations

import socket
import ssl
from pathlib import Path

import pytest
from pydantic import ValidationError

from kefe_api.core.settings import Settings
from kefe_api.infrastructure import provider_http_runtime as runtime
from kefe_api.modules.knowledge.provider_http_transport import (
    FinalProviderHttpError,
    PinnedOutboundHttpRequest,
    ProviderHttpMethod,
    RetryableProviderHttpError,
    UnconfiguredPinnedHttpBackend,
    UnconfiguredProviderDnsResolver,
)


class FakeHeaders:
    def __init__(self, pairs: tuple[tuple[str, str], ...] = ()) -> None:
        self._values: dict[str, list[str]] = {}
        for name, value in pairs:
            self._values.setdefault(name.lower(), []).append(value)

    def get_all(self, name: str):
        values = self._values.get(name.lower())
        return None if values is None else list(values)


class FakeResponse:
    def __init__(
        self,
        *,
        status: int = 200,
        version: int = 11,
        headers: tuple[tuple[str, str], ...] = (("content-type", "application/json"),),
        body: bytes = b"{}",
        read_error: Exception | None = None,
    ) -> None:
        self.status = status
        self.version = version
        self.headers = FakeHeaders(headers)
        self.body = body
        self.read_error = read_error
        self.read_amounts: list[int | None] = []

    def read(self, amount: int | None = None) -> bytes:
        self.read_amounts.append(amount)
        if self.read_error is not None:
            raise self.read_error
        if amount is None:
            return self.body
        return self.body[:amount]


class FakeConnection:
    def __init__(
        self,
        response: FakeResponse | None = None,
        *,
        endheaders_error: Exception | None = None,
        getresponse_error: Exception | None = None,
    ) -> None:
        self.response = response or FakeResponse()
        self.endheaders_error = endheaders_error
        self.getresponse_error = getresponse_error
        self.request: tuple[str, str, bool, bool] | None = None
        self.headers: list[tuple[str, tuple[str, ...]]] = []
        self.ended = False
        self.closed = False

    def putrequest(
        self,
        method: str,
        url: str,
        skip_host: bool = False,
        skip_accept_encoding: bool = False,
    ) -> None:
        self.request = (method, url, skip_host, skip_accept_encoding)

    def putheader(self, header: str, *values: str) -> None:
        self.headers.append((header, values))

    def endheaders(self) -> None:
        if self.endheaders_error is not None:
            raise self.endheaders_error
        self.ended = True

    def getresponse(self) -> FakeResponse:
        if self.getresponse_error is not None:
            raise self.getresponse_error
        return self.response

    def close(self) -> None:
        self.closed = True


class FakeConnectionFactory:
    def __init__(self, connection: FakeConnection) -> None:
        self.connection = connection
        self.requests: list[PinnedOutboundHttpRequest] = []
        self.contexts: list[ssl.SSLContext] = []

    def create(
        self,
        request: PinnedOutboundHttpRequest,
        context: ssl.SSLContext,
    ) -> FakeConnection:
        self.requests.append(request)
        self.contexts.append(context)
        return self.connection


class FakeRawSocket:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


class FakeTlsSocket:
    def __init__(self) -> None:
        self.timeout: float | None = None
        self.closed = False

    def settimeout(self, value: float) -> None:
        self.timeout = value

    def close(self) -> None:
        self.closed = True


class FakeSslContext:
    def __init__(self, tls_socket: FakeTlsSocket) -> None:
        self.tls_socket = tls_socket
        self.calls: list[tuple[object, str | None]] = []

    def wrap_socket(self, raw_socket, *, server_hostname=None):
        self.calls.append((raw_socket, server_hostname))
        return self.tls_socket


def _request(
    *,
    method: ProviderHttpMethod = ProviderHttpMethod.GET,
    max_response_bytes: int = 64,
) -> PinnedOutboundHttpRequest:
    return PinnedOutboundHttpRequest(
        adapter_code="test.provider_runtime.v1",
        method=method,
        host="api.example.com",
        port=443,
        target_ip="8.8.8.8",
        request_target="/feed?cursor=1",
        public_headers=(
            ("accept", "application/json"),
            ("user-agent", "KEFE-test"),
        ),
        connect_timeout_ms=750,
        read_timeout_ms=1250,
        max_response_bytes=max_response_bytes,
    )


def _backend(
    connection: FakeConnection,
    *,
    clock_values: tuple[int, ...] = (0, 5_000_000),
):
    values = iter(clock_values)
    factory = FakeConnectionFactory(connection)
    backend = runtime.PinnedTlsHttpBackend(
        connection_factory=factory,
        monotonic_clock=lambda: next(values),
    )
    return backend, factory


def _info(address: str):
    family = socket.AF_INET6 if ":" in address else socket.AF_INET
    socket_address = (address, 443, 0, 0) if family == socket.AF_INET6 else (address, 443)
    return (family, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", socket_address)


def test_settings_default_provider_http_runtime_is_disabled() -> None:
    settings = Settings()
    assert settings.provider_http_runtime_mode == "DISABLED"
    assert settings.provider_http_dns_max_answers == 16
    assert settings.provider_http_ca_bundle_path is None


def test_settings_reject_invalid_provider_http_runtime_values() -> None:
    with pytest.raises(ValidationError):
        Settings(provider_http_dns_max_answers=0)
    with pytest.raises(ValidationError):
        Settings(provider_http_dns_max_answers=65)
    with pytest.raises(ValidationError):
        Settings(provider_http_ca_bundle_path="   ")
    with pytest.raises(ValidationError):
        Settings(provider_http_runtime_mode="ON")


def test_disabled_runtime_composes_unconfigured_adapters() -> None:
    components = runtime.build_provider_http_runtime(Settings())
    assert isinstance(components.dns_resolver, UnconfiguredProviderDnsResolver)
    assert isinstance(components.backend, UnconfiguredPinnedHttpBackend)


def test_pinned_runtime_composes_system_resolver_and_tls_backend() -> None:
    components = runtime.build_provider_http_runtime(
        Settings(provider_http_runtime_mode="PINNED_TLS")
    )
    assert isinstance(components.dns_resolver, runtime.SystemProviderDnsResolver)
    assert isinstance(components.backend, runtime.PinnedTlsHttpBackend)


def test_system_dns_returns_all_deduplicated_candidates_without_authorizing() -> None:
    calls = []

    def getaddrinfo(*args, **kwargs):
        calls.append((args, kwargs))
        return [
            _info("10.0.0.1"),
            _info("8.8.8.8"),
            _info("10.0.0.1"),
            _info("2001:4860:4860::8888"),
        ]

    resolver = runtime.SystemProviderDnsResolver(
        max_answers=8,
        getaddrinfo=getaddrinfo,
    )
    assert resolver.resolve("api.example.com") == (
        "8.8.8.8",
        "10.0.0.1",
        "2001:4860:4860::8888",
    )
    assert calls[0][0][:2] == ("api.example.com", 443)


def test_system_dns_ip_literal_bypasses_system_resolution() -> None:
    resolver = runtime.SystemProviderDnsResolver(
        max_answers=4,
        getaddrinfo=lambda *args, **kwargs: pytest.fail("getaddrinfo must not run"),
    )
    assert resolver.resolve("8.8.4.4") == ("8.8.4.4",)


def test_system_dns_rejects_invalid_and_excessive_answers() -> None:
    invalid = runtime.SystemProviderDnsResolver(
        max_answers=4,
        getaddrinfo=lambda *args, **kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("bad", 443))
        ],
    )
    with pytest.raises(FinalProviderHttpError) as invalid_error:
        invalid.resolve("api.example.com")
    assert invalid_error.value.code == "PROVIDER_HTTP_DNS_INVALID"

    excessive = runtime.SystemProviderDnsResolver(
        max_answers=1,
        getaddrinfo=lambda *args, **kwargs: [_info("8.8.8.8"), _info("1.1.1.1")],
    )
    with pytest.raises(FinalProviderHttpError) as excessive_error:
        excessive.resolve("api.example.com")
    assert excessive_error.value.code == "PROVIDER_HTTP_DNS_TOO_MANY_ANSWERS"


def test_system_dns_maps_resolution_failure_without_exception_text() -> None:
    def unavailable(*args, **kwargs):
        raise socket.gaierror("private resolver detail")

    resolver = runtime.SystemProviderDnsResolver(
        max_answers=4,
        getaddrinfo=unavailable,
    )
    with pytest.raises(RetryableProviderHttpError) as caught:
        resolver.resolve("api.example.com")
    assert caught.value.code == "PROVIDER_HTTP_DNS_UNAVAILABLE"
    assert "private resolver detail" not in str(caught.value)


def test_exact_ip_connection_uses_selected_ip_and_approved_host_sni() -> None:
    raw_socket = FakeRawSocket()
    tls_socket = FakeTlsSocket()
    ssl_context = FakeSslContext(tls_socket)
    calls = []

    def socket_factory(address, timeout):
        calls.append((address, timeout))
        return raw_socket

    factory = runtime.SystemPinnedHttpsConnectionFactory(
        socket_factory=socket_factory,
    )
    connection = factory.create(_request(), ssl_context)  # type: ignore[arg-type]
    connection.connect()  # type: ignore[attr-defined]

    assert calls == [(('8.8.8.8', 443), 0.75)]
    assert ssl_context.calls == [(raw_socket, "api.example.com")]
    assert tls_socket.timeout == 1.25
    assert connection.sock is tls_socket  # type: ignore[attr-defined]


def test_ssl_context_requires_verification_and_tls12() -> None:
    context = runtime.build_provider_ssl_context(None)
    assert context.check_hostname is True
    assert context.verify_mode == ssl.CERT_REQUIRED
    assert context.minimum_version == ssl.TLSVersion.TLSv1_2
    if hasattr(ssl, "OP_NO_COMPRESSION"):
        assert context.options & ssl.OP_NO_COMPRESSION


def test_invalid_ca_bundle_fails_construction(tmp_path: Path) -> None:
    missing = tmp_path / "missing-ca.pem"
    with pytest.raises(RuntimeError, match="trust configuration is invalid"):
        runtime.PinnedTlsHttpBackend(ca_bundle_path=str(missing))


def test_backend_emits_exact_bounded_http11_request_and_projects_headers() -> None:
    response = FakeResponse(
        headers=(
            ("content-length", "2"),
            ("content-type", "application/json; charset=utf-8"),
            ("etag", '"v1"'),
            ("server", "must-not-project"),
            ("set-cookie", "must-not-project=1"),
        ),
        body=b"{}",
    )
    connection = FakeConnection(response)
    backend, factory = _backend(connection)

    result = backend.execute(_request())

    assert connection.request == ("GET", "/feed?cursor=1", True, True)
    assert connection.headers == [
        ("Host", ("api.example.com",)),
        ("Connection", ("close",)),
        ("Accept-Encoding", ("identity",)),
        ("accept", ("application/json",)),
        ("user-agent", ("KEFE-test",)),
    ]
    assert connection.ended is True
    assert connection.closed is True
    assert response.read_amounts == [65]
    assert result.status_code == 200
    assert result.headers == (
        ("content-type", "application/json; charset=utf-8"),
        ("etag", '"v1"'),
    )
    assert result.body == b"{}"
    assert result.elapsed_ms == 5
    assert factory.requests == [_request()]
    context = factory.contexts[0]
    assert context.check_hostname is True
    assert context.verify_mode == ssl.CERT_REQUIRED


def test_backend_rejects_unsupported_encoding_and_duplicate_projected_header() -> None:
    encoded, _ = _backend(
        FakeConnection(
            FakeResponse(headers=(("content-encoding", "gzip"),), body=b"data")
        )
    )
    with pytest.raises(FinalProviderHttpError) as encoded_error:
        encoded.execute(_request())
    assert encoded_error.value.code == "PROVIDER_HTTP_CONTENT_ENCODING_UNSUPPORTED"

    duplicate, _ = _backend(
        FakeConnection(
            FakeResponse(
                headers=(
                    ("content-type", "application/json"),
                    ("content-type", "text/plain"),
                )
            )
        )
    )
    with pytest.raises(FinalProviderHttpError) as duplicate_error:
        duplicate.execute(_request())
    assert duplicate_error.value.code == "PROVIDER_HTTP_PROTOCOL_INVALID"


def test_backend_enforces_content_length_and_max_plus_one_body_read() -> None:
    early_response = FakeResponse(
        headers=(("content-length", "65"),),
        body=b"not-read",
    )
    early, _ = _backend(FakeConnection(early_response))
    with pytest.raises(FinalProviderHttpError) as early_error:
        early.execute(_request(max_response_bytes=64))
    assert early_error.value.code == "PROVIDER_HTTP_RESPONSE_TOO_LARGE"
    assert early_response.read_amounts == []

    oversized_response = FakeResponse(
        headers=(("content-type", "application/octet-stream"),),
        body=b"x" * 66,
    )
    oversized, _ = _backend(FakeConnection(oversized_response))
    with pytest.raises(FinalProviderHttpError) as oversized_error:
        oversized.execute(_request(max_response_bytes=64))
    assert oversized_error.value.code == "PROVIDER_HTTP_RESPONSE_TOO_LARGE"
    assert oversized_response.read_amounts == [65]


def test_backend_rejects_ambiguous_framing_and_invalid_no_body_response() -> None:
    ambiguous, _ = _backend(
        FakeConnection(
            FakeResponse(
                headers=(
                    ("content-length", "2"),
                    ("transfer-encoding", "chunked"),
                ),
                body=b"{}",
            )
        )
    )
    with pytest.raises(FinalProviderHttpError) as ambiguous_error:
        ambiguous.execute(_request())
    assert ambiguous_error.value.code == "PROVIDER_HTTP_PROTOCOL_INVALID"

    invalid_204, _ = _backend(
        FakeConnection(FakeResponse(status=204, headers=(), body=b"unexpected"))
    )
    with pytest.raises(FinalProviderHttpError) as no_body_error:
        invalid_204.execute(_request())
    assert no_body_error.value.code == "PROVIDER_HTTP_PROTOCOL_INVALID"


def test_head_allows_representation_content_length_with_empty_body() -> None:
    backend, _ = _backend(
        FakeConnection(
            FakeResponse(
                headers=(("content-length", "42"),),
                body=b"",
            )
        )
    )
    result = backend.execute(_request(method=ProviderHttpMethod.HEAD))
    assert result.body == b""


def test_backend_maps_connect_tls_read_and_protocol_failures() -> None:
    cases = (
        (
            runtime._ConnectTimedOut(),
            RetryableProviderHttpError,
            "PROVIDER_HTTP_CONNECT_TIMEOUT",
        ),
        (
            runtime._ConnectUnavailable(),
            RetryableProviderHttpError,
            "PROVIDER_HTTP_UNAVAILABLE",
        ),
        (
            runtime._TlsRejected(),
            FinalProviderHttpError,
            "PROVIDER_HTTP_TLS_REJECTED",
        ),
        (
            socket.timeout("secret timeout detail"),
            RetryableProviderHttpError,
            "PROVIDER_HTTP_READ_TIMEOUT",
        ),
        (
            http_client_error(),
            FinalProviderHttpError,
            "PROVIDER_HTTP_PROTOCOL_INVALID",
        ),
    )
    for failure, error_type, code in cases:
        backend, _ = _backend(FakeConnection(endheaders_error=failure))
        with pytest.raises(error_type) as caught:
            backend.execute(_request())
        assert caught.value.code == code
        assert "secret timeout detail" not in str(caught.value)


def http_client_error():
    import http.client

    return http.client.BadStatusLine("private status line")


def test_backend_maps_incomplete_content_length_to_retryable_failure() -> None:
    backend, _ = _backend(
        FakeConnection(
            FakeResponse(
                headers=(
                    ("content-length", "3"),
                    ("content-type", "application/json"),
                ),
                body=b"{}",
            )
        )
    )
    with pytest.raises(RetryableProviderHttpError) as caught:
        backend.execute(_request())
    assert caught.value.code == "PROVIDER_HTTP_UNAVAILABLE"


def test_backend_always_closes_connection_on_response_failure() -> None:
    connection = FakeConnection(getresponse_error=socket.timeout("private"))
    backend, _ = _backend(connection)
    with pytest.raises(RetryableProviderHttpError):
        backend.execute(_request())
    assert connection.closed is True
