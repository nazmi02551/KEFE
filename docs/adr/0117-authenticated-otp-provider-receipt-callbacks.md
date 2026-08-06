# ADR-0117 — Authenticated OTP provider receipt callbacks

- Status: Accepted
- Date: 2026-08-06
- Wave: F4
- Capabilities: CAP-084, CAP-123

## Context

The production HTTP OTP adapter can prove only that a provider accepted or rejected the synchronous send request. Some providers later emit asynchronous delivery receipts, but an unauthenticated callback would allow forged delivery outcomes, replay storms and privacy leakage.

The callback must remain provider-neutral, work with rotation-safe secret references, converge under retries and restarts, and avoid turning provider payloads into a new user-identity datastore.

## Decision

KEFE exposes an internal provider callback at:

`POST /internal/provider/v1/otp-delivery-receipts`

The route is intentionally excluded from the consumer OpenAPI document. Its protocol is governed by `docs/contracts/otp-provider-receipts.v1.json` and an executable checker.

### Authentication

The provider supplies timestamp, key id, provider event id and signature headers. KEFE verifies HMAC-SHA256 over the exact bytes:

```text
v1\n{timestamp}\n{key_id}\n{provider_event_id}\n{exact_raw_body}
```

Signatures are compared in constant time. Timestamp skew, body size and header syntax are bounded before persistence.

A configured key id resolves an opaque secret reference on every callback through a bounded zeroing secret lease. Multiple key ids may overlap during rotation. Secret material and secret references are never persisted or returned.

### Receipt body

The body contains only:

- delivery UUID;
- normalized outcome: `DELIVERED`, `UNDELIVERABLE` or `EXPIRED`;
- provider occurrence time.

Additional fields are rejected. The raw body is used only for signature verification and is not stored.

### Privacy-safe persistence

KEFE stores only:

- SHA-256 of the high-entropy provider event id;
- SHA-256 of the canonical lowercase delivery UUID;
- normalized outcome;
- provider occurrence time;
- server receipt time.

The raw provider event id, raw delivery id, recipient, recipient hash, OTP, callback payload, signature, credentials, endpoint, account id, actor id, device id and session id are forbidden.

Receipt rows are append-only and retention-bounded. Direct `UPDATE` is rejected at the database layer.

### Idempotency and conflict

The provider-event digest is globally unique.

- An exact replay returns `202` with `duplicate=true`.
- Concurrent exact replays converge on one row.
- Reuse of the same event id with different delivery facts returns `409 AUTH_OTP_RECEIPT_EVENT_CONFLICT`.

### Failure behavior

- Disabled callback mode returns `404 AUTH_OTP_RECEIPT_DISABLED`.
- Retryable secret resolution failure returns `503 AUTH_OTP_RECEIPT_AUTH_UNAVAILABLE`.
- Invalid key id, signature, stale timestamp or malformed authentication returns the same privacy-preserving `401 AUTH_OTP_RECEIPT_REJECTED` response.
- No callback failure can trigger another OTP send or alter the original synchronous provider result.

## Consequences

KEFE gains a durable and provider-neutral authenticity/replay boundary for asynchronous receipts without claiming that a real provider has been connected.

This ADR does not prove real email or SMS delivery, provider callback transport availability, provider-specific semantic completeness, production key-rotation quality, deployed callback latency/SLO behavior, operator response effectiveness or user-visible delivery correlation.
