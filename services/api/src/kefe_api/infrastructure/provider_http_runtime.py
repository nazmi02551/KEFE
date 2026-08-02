from __future__ import annotations

import http.client
import ipaddress
import re
import socket
import ssl
from collections.abc import Callable
from dataclasses import dataclass
from time import monotonic_ns
from typing import Protocol

from kefe_api.core.settings import Settings
from kefe_api.modules.knowledge.provider_http_transport import (
    FinalProviderHttpError,
    PinnedHttpBackend,
    PinnedOutboundHttpRequest,
    ProviderDnsResolver,
    ProviderHttpError,
    ProviderHttpMethod,
    RawHttpResponse,
    RetryableProviderHttpError,
    UnconfiguredPinnedHttpBackend,
    UnconfiguredProviderDnsResolver,
)

_MAX_DNS_ANSWERS = 64
_RESPONSE_HEADER_ALLOWLIST = (
    "content-type",
    "etag",
    "last-modified",
    "location",
    "retry-after",
)
_DECIMAL = re.compile(r"^[0-9]+$")


class _ConnectTimedOut(Exception):
    pass


class _ConnectUnavailable(Exception):
    pass


class _TlsRejected(Exception):
    pass


class HttpsResponse(Protocol):
    status: int
    version: int
    headers: object

    def read(self, amount: int | None = None) -> bytes: ...


class PinnedHttpsConnection(Protocol):
    def putrequest(
        self,
        method: str,
        url: str,
        skip_host: bool = False,
        skip_accept_encoding: bool = False,
    ) -> None: ...

    def putheader(self, header: str, *values: str) -> None: ...

    def endheaders(self) -> None: ...

    def getresponse(self) -> HttpsResponse: ...

    def close(self) -> None: ...


class PinnedHttpsConnectionFactory(Protocol):
    def create(
        self,
        request: PinnedOutboundHttpRequest,
        context: ssl.SSLContext,
    ) -> PinnedHttpsConnection: ...


class SystemProviderDnsResolver:
    def __init__(
        self,
        *,
        max_answers: int,
        getaddrinfo: Callable[..., list[tuple[object, ...]]] = socket.getaddrinfo,
    ) -> None:
        if not 1 <= max_answers <= _MAX_DNS_ANSWERS:
            raise ValueError("provider HTTP DNS max_answers is outside the supported range")
        self._max_answers = max_answers
        self._getaddrinfo = getaddrinfo

    def resolve(self, host: str) -> tuple[str, ...]:
        if not host or host != host.strip():
            raise FinalProviderHttpError("PROVIDER_HTTP_DNS_INVALID")
        try:
            literal = ipaddress.ip_address(host)
        except ValueError:
            literal = None
        if literal is not None:
            return (str(literal),)

        try:
            results = self._getaddrinfo(
                host,
                443,
                family=socket.AF_UNSPEC,
                type=socket.SOCK_STREAM,
                proto=socket.IPPROTO_TCP,
                flags=getattr(socket, "AI_ADDRCONFIG", 0),
            )
        except (socket.gaierror, TimeoutError, OSError) as exc:
            raise RetryableProviderHttpError("PROVIDER_HTTP_DNS_UNAVAILABLE") from exc
        except Exception as exc:
            raise RetryableProviderHttpError("PROVIDER_HTTP_DNS_UNAVAILABLE") from exc

        addresses: set[ipaddress.IPv4Address | ipaddress.IPv6Address] = set()
        for result in results:
            if len(result) != 5:
                raise FinalProviderHttpError("PROVIDER_HTTP_DNS_INVALID")
            socket_address = result[4]
            if not isinstance(socket_address, tuple) or not socket_address:
                raise FinalProviderHttpError("PROVIDER_HTTP_DNS_INVALID")
            candidate = socket_address[0]
            if not isinstance(candidate, str):
                raise FinalProviderHttpError("PROVIDER_HTTP_DNS_INVALID")
            try:
                addresses.add(ipaddress.ip_address(candidate))
            except ValueError as exc:
                raise FinalProviderHttpError("PROVIDER_HTTP_DNS_INVALID") from exc
            if len(addresses) > self._max_answers:
                raise FinalProviderHttpError(
                    "PROVIDER_HTTP_DNS_TOO_MANY_ANSWERS"
                )

        if not addresses:
            raise RetryableProviderHttpError("PROVIDER_HTTP_DNS_UNAVAILABLE")
        ordered = sorted(
            addresses,
            key=lambda address: (address.version, address.packed),
        )
        return tuple(str(address) for address in ordered)


class _ExactIpHttpsConnection(http.client.HTTPSConnection):
    def __init__(
        self,
        *,
        request: PinnedOutboundHttpRequest,
        context: ssl.SSLContext,
        socket_factory: Callable[..., socket.socket],
    ) -> None:
        super().__init__(
            host=request.host,
            port=request.port,
            timeout=request.connect_timeout_ms / 1000,
            context=context,
        )
        self._target_ip = request.target_ip
        self._read_timeout_seconds = request.read_timeout_ms / 1000
        self._socket_factory = socket_factory

    def connect(self) -> None:
        raw_socket: socket.socket | None = None
        try:
            raw_socket = self._socket_factory(
                (self._target_ip, self.port),
                self.timeout,
            )
        except (TimeoutError, socket.timeout) as exc:
            raise _ConnectTimedOut from exc
        except OSError as exc:
            raise _ConnectUnavailable from exc

        try:
            tls_socket = self._context.wrap_socket(
                raw_socket,
                server_hostname=self.host,
            )
            tls_socket.settimeout(self._read_timeout_seconds)
        except (ssl.SSLCertVerificationError, ssl.SSLError) as exc:
            raw_socket.close()
            raise _TlsRejected from exc
        except (TimeoutError, socket.timeout) as exc:
            raw_socket.close()
            raise _ConnectTimedOut from exc
        except OSError as exc:
            raw_socket.close()
            raise _ConnectUnavailable from exc
        self.sock = tls_socket


class SystemPinnedHttpsConnectionFactory:
    def __init__(
        self,
        *,
        socket_factory: Callable[..., socket.socket] = socket.create_connection,
    ) -> None:
        self._socket_factory = socket_factory

    def create(
        self,
        request: PinnedOutboundHttpRequest,
        context: ssl.SSLContext,
    ) -> PinnedHttpsConnection:
        return _ExactIpHttpsConnection(
            request=request,
            context=context,
            socket_factory=self._socket_factory,
        )


def build_provider_ssl_context(ca_bundle_path: str | None) -> ssl.SSLContext:
    if ca_bundle_path is not None and not ca_bundle_path.strip():
        raise RuntimeError("provider HTTP CA bundle path must not be blank")
    try:
        context = ssl.create_default_context(cafile=ca_bundle_path)
    except (OSError, ssl.SSLError) as exc:
        raise RuntimeError("provider HTTP trust configuration is invalid") from exc
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.check_hostname = True
    context.verify_mode = ssl.CERT_REQUIRED
    if hasattr(ssl, "OP_NO_COMPRESSION"):
        context.options |= ssl.OP_NO_COMPRESSION
    return context


def _header_values(headers: object, name: str) -> tuple[str, ...]:
    getter = getattr(headers, "get_all", None)
    if getter is None:
        raise FinalProviderHttpError("PROVIDER_HTTP_PROTOCOL_INVALID")
    values = getter(name)
    if values is None:
        return ()
    if not isinstance(values, list):
        values = list(values)
    if any(not isinstance(value, str) for value in values):
        raise FinalProviderHttpError("PROVIDER_HTTP_PROTOCOL_INVALID")
    return tuple(values)


def _single_header(headers: object, name: str) -> str | None:
    values = _header_values(headers, name)
    if len(values) > 1:
        raise FinalProviderHttpError("PROVIDER_HTTP_PROTOCOL_INVALID")
    if not values:
        return None
    value = values[0].strip()
    if "\r" in value or "\n" in value:
        raise FinalProviderHttpError("PROVIDER_HTTP_PROTOCOL_INVALID")
    return value


def _validate_framing(headers: object, max_response_bytes: int) -> int | None:
    content_encoding = _single_header(headers, "content-encoding")
    if content_encoding is not None and content_encoding.lower() != "identity":
        raise FinalProviderHttpError(
            "PROVIDER_HTTP_CONTENT_ENCODING_UNSUPPORTED"
        )

    transfer_encoding = _single_header(headers, "transfer-encoding")
    if transfer_encoding is not None and transfer_encoding.lower() != "chunked":
        raise FinalProviderHttpError("PROVIDER_HTTP_PROTOCOL_INVALID")

    content_length = _single_header(headers, "content-length")
    if transfer_encoding is not None and content_length is not None:
        raise FinalProviderHttpError("PROVIDER_HTTP_PROTOCOL_INVALID")
    if content_length is None:
        return None
    if _DECIMAL.fullmatch(content_length) is None:
        raise FinalProviderHttpError("PROVIDER_HTTP_PROTOCOL_INVALID")
    parsed_length = int(content_length)
    if parsed_length > max_response_bytes:
        raise FinalProviderHttpError("PROVIDER_HTTP_RESPONSE_TOO_LARGE")
    return parsed_length


def _project_headers(headers: object) -> tuple[tuple[str, str], ...]:
    projected: list[tuple[str, str]] = []
    for name in _RESPONSE_HEADER_ALLOWLIST:
        value = _single_header(headers, name)
        if value is not None:
            projected.append((name, value))
    return tuple(projected)


def _host_header(host: str, port: int) -> str:
    rendered = f"[{host}]" if ":" in host else host
    if port == 443:
        return rendered
    return f"{rendered}:{port}"


class PinnedTlsHttpBackend:
    def __init__(
        self,
        *,
        ca_bundle_path: str | None = None,
        connection_factory: PinnedHttpsConnectionFactory | None = None,
        monotonic_clock: Callable[[], int] = monotonic_ns,
    ) -> None:
        self._context = build_provider_ssl_context(ca_bundle_path)
        self._connections = connection_factory or SystemPinnedHttpsConnectionFactory()
        self._monotonic_clock = monotonic_clock

    def execute(self, request: PinnedOutboundHttpRequest) -> RawHttpResponse:
        if request.method not in {ProviderHttpMethod.GET, ProviderHttpMethod.HEAD}:
            raise FinalProviderHttpError("PROVIDER_HTTP_PROTOCOL_INVALID")
        started_ns = self._monotonic_clock()
        connection = self._connections.create(request, self._context)
        try:
            connection.putrequest(
                request.method.value,
                request.request_target,
                skip_host=True,
                skip_accept_encoding=True,
            )
            connection.putheader("Host", _host_header(request.host, request.port))
            connection.putheader("Connection", "close")
            connection.putheader("Accept-Encoding", "identity")
            for name, value in request.public_headers:
                normalized = name.strip().lower()
                if normalized in {"host", "connection", "accept-encoding"}:
                    raise FinalProviderHttpError("PROVIDER_HTTP_PROTOCOL_INVALID")
                connection.putheader(name, value)
            connection.endheaders()
            response = connection.getresponse()
            if response.version not in {10, 11}:
                raise FinalProviderHttpError("PROVIDER_HTTP_PROTOCOL_INVALID")
            content_length = _validate_framing(
                response.headers,
                request.max_response_bytes,
            )
            body = response.read(request.max_response_bytes + 1)
            if not isinstance(body, bytes):
                raise FinalProviderHttpError("PROVIDER_HTTP_PROTOCOL_INVALID")
            if len(body) > request.max_response_bytes:
                raise FinalProviderHttpError("PROVIDER_HTTP_RESPONSE_TOO_LARGE")
            if (
                request.method is ProviderHttpMethod.GET
                and response.status not in {204, 304}
                and content_length is not None
                and len(body) != content_length
            ):
                raise RetryableProviderHttpError("PROVIDER_HTTP_UNAVAILABLE")
            if response.status in {204, 304} and body:
                raise FinalProviderHttpError("PROVIDER_HTTP_PROTOCOL_INVALID")
            projected_headers = _project_headers(response.headers)
            elapsed_ms = max(
                0,
                int((self._monotonic_clock() - started_ns) / 1_000_000),
            )
            try:
                return RawHttpResponse(
                    status_code=response.status,
                    headers=projected_headers,
                    body=body,
                    elapsed_ms=elapsed_ms,
                )
            except ValueError as exc:
                raise FinalProviderHttpError(
                    "PROVIDER_HTTP_PROTOCOL_INVALID"
                ) from exc
        except ProviderHttpError:
            raise
        except _ConnectTimedOut as exc:
            raise RetryableProviderHttpError(
                "PROVIDER_HTTP_CONNECT_TIMEOUT"
            ) from exc
        except _ConnectUnavailable as exc:
            raise RetryableProviderHttpError("PROVIDER_HTTP_UNAVAILABLE") from exc
        except _TlsRejected as exc:
            raise FinalProviderHttpError("PROVIDER_HTTP_TLS_REJECTED") from exc
        except (TimeoutError, socket.timeout) as exc:
            raise RetryableProviderHttpError("PROVIDER_HTTP_READ_TIMEOUT") from exc
        except (http.client.RemoteDisconnected, http.client.IncompleteRead) as exc:
            raise RetryableProviderHttpError("PROVIDER_HTTP_UNAVAILABLE") from exc
        except (http.client.HTTPException, ssl.SSLError, ValueError) as exc:
            raise FinalProviderHttpError("PROVIDER_HTTP_PROTOCOL_INVALID") from exc
        except OSError as exc:
            raise RetryableProviderHttpError("PROVIDER_HTTP_UNAVAILABLE") from exc
        except Exception as exc:
            raise RetryableProviderHttpError("PROVIDER_HTTP_UNAVAILABLE") from exc
        finally:
            connection.close()


@dataclass(frozen=True, slots=True)
class ProviderHttpRuntimeComponents:
    dns_resolver: ProviderDnsResolver
    backend: PinnedHttpBackend


def build_provider_http_runtime(settings: Settings) -> ProviderHttpRuntimeComponents:
    mode = settings.provider_http_runtime_mode
    if mode == "DISABLED":
        return ProviderHttpRuntimeComponents(
            dns_resolver=UnconfiguredProviderDnsResolver(),
            backend=UnconfiguredPinnedHttpBackend(),
        )
    if mode == "PINNED_TLS":
        return ProviderHttpRuntimeComponents(
            dns_resolver=SystemProviderDnsResolver(
                max_answers=settings.provider_http_dns_max_answers
            ),
            backend=PinnedTlsHttpBackend(
                ca_bundle_path=settings.provider_http_ca_bundle_path
            ),
        )
    raise RuntimeError("unsupported provider HTTP runtime mode")
