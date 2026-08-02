# ADR-0082 — Pinned DNS/TLS runtime and explicit egress activation

**Status:** Accepted  
**Date:** 2026-08-02  
**Issue:** #217  
**Parent:** ADR-0081 / PR #216

## Context

ADR-0081 established provider-neutral adoption profiles, exact HTTPS origin policy, public-address validation, deterministic IP pinning, redirect revalidation and bounded transport results. Production composition intentionally remained inert: it supplied an empty adoption registry plus unconfigured DNS and backend ports.

A concrete provider must not be adopted until the runtime can preserve the selected IP through the TCP connection and preserve the approved host through TLS SNI and certificate verification. A generic HTTP client that silently re-resolves DNS, follows redirects, reads proxy environment variables or accepts unbounded responses would break ADR-0081.

## Decision

1. Runtime activation is exact and explicit: `DISABLED` or `PINNED_TLS`. The default is `DISABLED`.
2. `DISABLED` composes the existing unconfigured DNS and backend adapters. `PINNED_TLS` composes a bounded system DNS adapter and a pinned TLS HTTP/1.1 backend.
3. Activating the network runtime does not authorize any provider. The adoption registry remains empty until a later provider-adoption contract registers an exact versioned profile.
4. System DNS returns deduplicated IP literals only, caps the number of answers and never decides whether an address is allowed. ADR-0081 remains the authorization layer and rejects every non-public result.
5. The backend connects to the exact `target_ip` selected by ADR-0081. It never reconnects by hostname and never performs DNS resolution.
6. TLS uses the approved request host as SNI and certificate hostname/IP verification identity. Verification is mandatory, TLS 1.2 is the minimum, TLS compression is disabled and there is no insecure fallback.
7. Trust roots come from the system trust store or one explicit CA bundle path. Invalid trust configuration fails construction rather than degrading verification.
8. The backend emits one HTTP/1.1 GET or HEAD request with no body, an exact Host header, `Connection: close` and `Accept-Encoding: identity`.
9. The backend does not consult proxy environment variables, create CONNECT tunnels, retain cookies, follow redirects or source ambient credentials.
10. Response handling is bounded. Projected response headers are limited to `content-type`, `location`, `etag`, `last-modified` and `retry-after`; duplicate projected singleton headers, unsupported content encodings, invalid Content-Length and oversized bodies fail closed. The body is read at most `max_response_bytes + 1`.
11. Runtime exceptions are mapped to bounded retryable/final codes. Exception text, URLs, IPs, headers and bodies do not enter operational results.
12. CI uses injected DNS/socket/TLS/HTTP doubles. No live external request is required or claimed.

## Consequences

- DNS rebinding remains blocked because resolution and authorization happen before an exact-IP connection.
- TLS still verifies the approved logical host rather than the selected IP endpoint.
- Provider egress stays impossible by default and remains impossible after `PINNED_TLS` activation until an exact adoption profile is registered.
- This slice proves runtime mechanics, not deployed firewall/VPC/NAT controls, provider terms compliance, credential injection or a successful external provider call.

## Rejected alternatives

- Generic URL fetch libraries with implicit DNS, redirects or proxy inheritance.
- Connecting to the hostname after separately validating an IP.
- Disabling certificate or hostname verification for development.
- Treating network runtime activation as provider authorization.
- Live internet CI as the primary correctness proof.
