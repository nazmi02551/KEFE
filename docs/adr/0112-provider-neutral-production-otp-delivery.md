# ADR-0112: Provider-neutral production OTP delivery

- **Status:** Accepted
- **Date:** 2026-08-05
- **Foundation phase:** F4
- **Capability:** CAP-084
- **Issue:** #320
- **Parent decisions:** ADR-0110, ADR-0111

## Context

KEFE has durable OTP challenges, verification consumption, account conversion replay, source-session rotation and replay-key rotation. Production composition nevertheless installs `DisabledOtpDelivery`, so the identity runtime cannot deliver an OTP outside development.

Selecting a vendor-specific email/SMS SDK would couple the account runtime to one provider and would not by itself establish safe timeout, retry, idempotency, redaction or startup behavior. The public account API must remain provider-neutral.

## Decision

### Explicit runtime modes

OTP delivery has three explicit modes:

- `CAPTURE`: development/test only; captures codes in-process and never exposes them through HTTP or object representation;
- `DISABLED`: non-production fail-closed adapter;
- `HTTP`: provider-neutral production adapter.

Production startup rejects `CAPTURE` and `DISABLED`. `HTTP` mode requires an HTTPS endpoint and a secret-managed bearer credential.

### Delivery identity and payload

The already-persisted `OtpChallenge.id` is the delivery identity. `OtpDeliveryPort.send` receives:

- `delivery_id` — challenge UUID;
- `channel` — `EMAIL` or `SMS`;
- normalized recipient;
- six-digit OTP code;
- challenge expiry.

The HTTP adapter sends a deterministic JSON object:

```json
{
  "channel": "EMAIL",
  "code": "123456",
  "delivery_id": "uuid",
  "expires_at": "UTC ISO-8601",
  "recipient": "normalized destination"
}
```

The same UUID is sent as `Idempotency-Key`. Every retry reuses the exact same request object, body and key.

### Transport constraints

The configured endpoint must:

- use HTTPS;
- use port 443 or the implicit HTTPS port;
- contain an explicit path;
- contain no userinfo, query or fragment;
- use an ASCII public DNS hostname;
- not use localhost, `.local`, a single-label hostname or an IP literal.

Redirects are not followed. Timeout, response-body budget and attempt count are bounded by validated settings. The response body is read only up to the configured limit and is never surfaced.

### Outcome mapping

- Any `2xx` response is accepted.
- Network failures and HTTP `408`, `425`, `429`, `500`, `502`, `503`, `504` are retryable up to the configured attempt limit.
- Exhausted retryable outcomes map to retryable `AUTH_OTP_DELIVERY_UNAVAILABLE` with HTTP 503.
- Other status codes and final transport violations map to non-retryable `AUTH_OTP_DELIVERY_REJECTED` with HTTP 502.

Provider response bodies, recipient values, OTP codes, bearer credentials and endpoint values are absent from domain errors, representations and operational results.

### Observability boundary

The adapter emits a non-sensitive operational result containing only:

- outcome;
- channel;
- attempt count;
- provider status code when available;
- bounded internal error code.

The repository provides a no-op observer and an in-memory evidence observer. A deployed metrics/alerting backend remains an external F4 gate.

### Public contract

The public OTP request, OTP verify and guest-merge request/response schemas do not change. No provider identifier or provider response is returned to the consumer.

## Rejected alternatives

### Vendor SDK inside the account service

Rejected because it couples domain logic to one provider and spreads provider error semantics into the account runtime.

### Persist plaintext OTP delivery jobs

Rejected for this slice because it creates a new sensitive durable queue. The existing challenge is persisted before delivery and the bounded adapter retry uses the challenge UUID as the natural idempotency key. A future durable delivery outbox would require its own encrypted/minimized-data decision.

### Automatic email/SMS fallback

Rejected because silent channel switching changes user intent, consent, cost and abuse controls.

### Follow redirects

Rejected because credentials and OTP payloads must never be forwarded to a different origin.

## Consequences

- Production composition now has an operable provider-neutral boundary instead of a permanently disabled adapter.
- A real provider can be integrated by implementing the accepted HTTP contract without changing account APIs.
- Repository CI proves request construction, bounded retries, redaction, composition and transport invocation; it does not prove real provider deliverability, production credentials, deployed DNS/network policy, SLO or operator rollback.
- CAP-084 and F4 remain partial until real provider deployment and external operational evidence exist.

## Verification

The exact runtime head must prove:

- challenge UUID and expiry propagation;
- deterministic JSON and idempotency header;
- same-request retry behavior;
- retryable and final outcome mapping;
- endpoint, secret, timeout, response and attempt validation;
- no sensitive data in repr/errors/operational facts;
- real `urllib` POST invocation through a controlled fake opener;
- production startup fail-closed and explicit HTTP activation;
- exact OpenAPI no-drift;
- existing account replay, privacy, PostgreSQL and mobile/global regressions.