# ADR-0113 — Durable OTP Request Abuse Guard

**Status:** Accepted implementation candidate  
**Date:** 2026-08-05  
**Capabilities:** CAP-084  
**Foundation wave:** F4

## Context

KEFE already bounds incorrect OTP verification attempts and, through ADR-0112, has an operable provider-neutral production delivery boundary. The remaining request-side gap is that every syntactically valid `POST /v1/auth/otp/request` can create and dispatch a fresh challenge.

That gap permits destination bombing, provider-cost amplification and races where concurrent requests for the same destination all pass before any process-local limiter observes the others. A process-local-only limiter is insufficient because production may restart or run multiple API instances.

The guard must not introduce an account-existence oracle, persist plaintext email/phone values, expose OTP codes, or claim that CI proves deployed anti-abuse effectiveness.

## Decision

### 1. Guard identity

Admission is keyed by:

`(OtpChannel, sha256(channel + ':' + normalized_destination))`

Canonical destination normalization happens before the hash is built. The guard therefore treats email case/outer whitespace variants as one destination without storing the destination itself.

The guard never checks whether the destination already owns an account. Limited and non-limited behavior is independent of account existence.

### 2. Runtime mode

`KEFE_OTP_REQUEST_GUARD_MODE` supports:

- `AUTO`: enforce in production; remain off in non-production for compatibility with deterministic development fixtures and existing tests;
- `ENFORCE`: enforce in any environment;
- `OFF`: allowed only outside production.

Production startup fails closed when mode is explicitly `OFF`.

### 3. Policy

The initial configurable policy is:

- minimum cooldown: 60 seconds;
- rolling window: 15 minutes;
- maximum admitted requests in one window: 5;
- guard retention: 24 hours.

The window cannot be shorter than the cooldown and retention cannot be shorter than the window.

A provider failure after admission still consumes the request. Releasing quota on transport failure would permit outage-amplified retry storms and duplicate provider work when the provider accepted a request but the response was lost.

### 4. Atomic persistence

PostgreSQL stores one row per channel/hash in `identity.otp_request_guard`.

The repository transaction:

1. lazily prunes expired guard rows;
2. inserts the candidate OTP challenge;
3. creates or locks the channel/hash guard row;
4. evaluates cooldown/window policy;
5. updates the guard and commits the challenge only when admitted.

A rejected request raises `AUTH_RATE_LIMITED`; the surrounding transaction rolls back the candidate challenge insert. Concurrent inserts serialize through the guard primary key and row lock, so at most one request is admitted inside the cooldown.

The in-memory implementation applies the same semantics under one re-entrant lock. It is evidence and local-runtime support, not a distributed production limiter.

### 5. Privacy and retention

The guard stores only:

- channel;
- destination hash;
- latest challenge UUID;
- window/cooldown timestamps;
- request count;
- retention/update timestamps.

It stores no plaintext destination, hint, OTP code, code hash, provider request or provider response.

`latest_challenge_id` references `identity.otp_challenge(id)` with `ON DELETE CASCADE`. Account privacy deletion already deletes all OTP challenges for the account identifier; deleting the latest challenge therefore removes the guard row in the same privacy transaction. Non-account guard rows are bounded by retention and pruned during later admissions.

### 6. Public error

The existing registered error is reused:

- code: `AUTH_RATE_LIMITED`;
- status: `429`;
- retryable: `true`.

No destination value, account state or detailed threshold state is returned. This slice does not add `Retry-After`; an exact retry time could become a useful abuse oracle and requires a separately governed response-header decision.

## Alternatives rejected

### Process-local dictionary only

Rejected because it resets after restart and cannot coordinate multiple API processes.

### Rate limit by plaintext destination

Rejected because the limiter does not require reusable contact data and must remain privacy-minimal.

### IP-only rate limiting

Rejected as the primary control because proxy trust, NAT aggregation, IPv6 prefix policy and privacy retention are unresolved. IP/device controls remain a separate defense-in-depth slice.

### Release quota when provider delivery fails

Rejected because a lost provider response cannot prove that no message was accepted, and automatic release can multiply provider traffic during outages.

### CAPTCHA in the API contract

Rejected for this slice. CAPTCHA/proof-of-work affects consumer UX, accessibility, vendor dependency and regional privacy requirements and needs an explicit product decision.

## Consequences

- Production obtains a restart-durable destination-level guard without changing the success API.
- Existing non-production fixtures remain compatible under `AUTO`.
- Same-destination races converge to one admitted challenge.
- Thresholds are configurable but are not claimed to be production-tuned.
- This is one defense layer; it does not replace edge, IP/device, provider or anomaly controls.

## Evidence boundary

CI may prove deterministic policy, atomic PostgreSQL behavior, restart durability, privacy-minimal schema, deletion cascade and unchanged OpenAPI.

CI does **not** prove:

- real-world abuse resistance;
- production threshold quality;
- IP/device/edge protection;
- provider deliverability or provider-side idempotency;
- deployed SLO, alerting, incident response or operator rollback.
