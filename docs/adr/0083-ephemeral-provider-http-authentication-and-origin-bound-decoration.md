# ADR-0083 — Ephemeral provider HTTP authentication and origin-bound decoration

- Status: Accepted
- Date: 2026-08-02
- Parent: ADR-0080, ADR-0081, ADR-0082
- Issue: #219

## Context

KEFE now has permit-scoped secret leases, controlled provider HTTP policy and an exact-IP pinned TLS runtime. Credential values still must not enter URLs, public request models, persistent registries, operational results, logs or exception text. Adding `Authorization` or API-key strings directly to `OutboundHttpRequest` would create long-lived immutable copies and would allow redirects to carry credentials to another approved origin.

## Decision

1. Authentication is configured by an immutable exact profile keyed by versioned `adapter_code`.
2. The first exact schemes are `BEARER_AUTHORIZATION` and `HEADER_TOKEN`.
3. Every auth profile binds one exact HTTPS credential origin. The origin must also be present in the provider adoption profile before execution can succeed.
4. `BEARER_AUTHORIZATION` always uses the lowercase `authorization` header and a fixed `Bearer ` prefix. `HEADER_TOKEN` uses one exact normalized header name that passes a strict denylist.
5. Secret material is accepted only through the existing callback-scoped `SecretAccess.use_bytes` port. It is never decoded to text.
6. Secret bytes must be non-empty visible ASCII without whitespace, control bytes, CR or LF and must remain within the profile byte budget.
7. The auth layer owns a mutable sensitive-header buffer. It exposes callback-scoped read-only memoryviews, redacts repr, forbids equality/hash/serialization and zeroizes its owned buffer on close.
8. The transport and pinned backend receive only a sensitive-header access port, never raw credential strings or bytes in public request models.
9. The pinned backend validates sensitive header names again. It emits the sensitive header and calls `endheaders` inside the access callback.
10. Credentials may be reused across same-origin redirects. A redirect that changes origin fails closed before another backend request with `PROVIDER_HTTP_AUTH_REDIRECT_BLOCKED`.
11. Production composition creates an empty auth-profile registry and a secure executor. Therefore no credential-bearing request can be authorized until a later explicit adoption slice registers both adoption and auth profiles.
12. Operational results remain unchanged and contain no auth scheme, credential origin, header name or secret-derived data.

## Owned-buffer honesty boundary

KEFE proves deterministic zeroization only for mutable buffers it owns. It does not claim deterministic erasure of temporary copies created inside the Python interpreter, `http.client`, OpenSSL/TLS libraries, the kernel socket stack or remote systems. The design minimizes scope and persistence but does not overstate process-wide erasure guarantees.

## Consequences

- Provider adapters can request authenticated HTTP without receiving raw secret bytes as persistent state.
- Cross-origin redirect credential forwarding is structurally blocked.
- Real OAuth flows, request signing/HMAC, cookies, query credentials and provider-specific adoption remain out of scope.
- A later real-provider slice must register exact adoption and auth profiles and provide external terms/rate-limit evidence without weakening these boundaries.
