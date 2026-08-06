# F4 — OTP Provider Receipt Callback Checkpoint

- Date: 2026-08-06
- Wave: F4
- Capabilities: CAP-084, CAP-123
- Status: IMPLEMENTED_PARTIAL
- Issue: #330
- Pull request: #331

## Implemented boundary

This slice adds a provider-neutral asynchronous OTP receipt callback protected by exact-body HMAC-SHA256 authentication.

The boundary provides:

- timestamp, key-id and high-entropy provider-event-id headers;
- strict clock-skew, body-size and header syntax bounds;
- opaque secret-reference resolution through bounded zeroing leases;
- overlapping key ids for rotation without process restart;
- constant-time signature comparison;
- exact replay convergence;
- conflicting event-id reuse rejection;
- append-only memory and PostgreSQL persistence;
- retention pruning;
- aggregate delivery facts;
- direct PostgreSQL UPDATE rejection;
- no consumer OpenAPI change.

## Privacy boundary

Persisted records contain only:

- SHA-256 provider-event reference;
- SHA-256 canonical delivery reference;
- normalized outcome;
- occurrence time;
- receipt time.

They do not contain recipient, destination/hash, OTP/hash, raw body, signature, credential, secret reference, provider endpoint, raw delivery id, raw provider event id, account, actor, device or session identity.

## Evidence target

Dedicated CI must prove:

- exact-body signature acceptance;
- invalid signature, stale timestamp and unknown key indistinguishability;
- disabled fail-closed behavior;
- exact replay idempotency;
- conflicting replay rejection;
- restart durability;
- concurrent convergence;
- retention pruning;
- privacy-safe schema;
- immutable PostgreSQL records;
- parent OTP delivery, secret, health, alert, merge and privacy regressions;
- exact composed OpenAPI remains unchanged.

## Explicit non-claims

This checkpoint does not prove:

- a real email/SMS provider is connected;
- provider callback transport availability;
- provider-specific semantic completeness;
- production key-rotation quality;
- deployed callback latency or SLO behavior;
- operator incident response effectiveness;
- user-visible delivery correlation.
