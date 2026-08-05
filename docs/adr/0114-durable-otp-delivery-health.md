# ADR-0114 — Durable OTP Delivery Health Signal

**Status:** Accepted implementation candidate  
**Date:** 2026-08-05  
**Capabilities:** CAP-084, CAP-123  
**Foundation wave:** F4

## Context

ADR-0112 introduced provider-neutral HTTP OTP delivery and classified each final provider interaction as `ACCEPTED`, `UNAVAILABLE` or `REJECTED`. The adapter can emit `OtpDeliveryOperationalResult`, but production composition previously supplied no observer, so results disappeared after the request completed.

That made it impossible for the existing secured Admin operational report to distinguish:

- a quiet OTP channel with no traffic;
- normal accepted traffic;
- repeated temporary provider failures;
- repeated permanent provider rejection.

The operational signal must remain privacy-minimal. It must not become a recipient-level activity log, expose OTP codes, retain provider payloads or turn provider acceptance into a claim that a user actually received a message.

## Decision

### 1. Observe only the final provider-neutral result

`HttpOtpDelivery` continues to own provider execution and retry classification. After its final result is known, the configured observer receives only:

- channel;
- final outcome;
- number of attempts;
- bounded HTTP status code, when present;
- bounded operational error code, when present.

No recipient, challenge UUID, delivery UUID, OTP code, request body, response body, bearer credential or provider endpoint is passed to the durable health repository.

Development `CAPTURE` and explicitly disabled delivery do not manufacture provider health events. Their absence is represented as `QUIET`, meaning only that no HTTP delivery result was observed in the selected window.

### 2. Observation is fail-open relative to delivery semantics

Health persistence is wrapped by `FailOpenOtpDeliveryObserver`.

If the health repository fails:

- an accepted provider response remains accepted;
- the original provider `DomainError` remains authoritative;
- no second provider call is made;
- the failure is logged without a delivery payload;
- the missing event is accepted as a bounded telemetry gap.

This is deliberately different from fail-closed security controls. Operational telemetry must never create duplicate OTP sends or mask the real provider outcome.

### 3. Append-only, aggregate-safe persistence

PostgreSQL stores events in `identity.otp_delivery_event` with no foreign keys or user identifiers. Rows contain only:

- generated event UUID;
- observation time;
- channel;
- outcome;
- attempt count;
- bounded status/error code;
- creation time.

The table is append-only except for retention deletion. There is no update path and no relationship to account, guest, challenge or verification records.

The default retention is seven days. Expired rows are pruned on both event append and snapshot read. This is lazy operational retention: it is enforced whenever the feature is used, but CI does not claim an always-running external deletion scheduler.

### 4. Policy-driven snapshot

The internal snapshot evaluates a 15-minute window and exposes four signals:

- `QUIET`: no observed HTTP delivery result in the window;
- `NOMINAL`: observed traffic without an active threshold reason;
- `ATTENTION`: an attention count or ratio threshold is reached;
- `CRITICAL`: a critical count or ratio threshold is reached.

Default thresholds are:

- total failed deliveries: attention 3, critical 10;
- temporary unavailability: attention 2, critical 5;
- failure ratio: attention 20%, critical 50%;
- minimum sample before ratio evaluation: 5.

A ratio is not calculated below the minimum sample size. This prevents one isolated failure in a low-volume window from automatically producing a percentage-based incident signal. Count thresholds remain independently active.

The snapshot also contains aggregate facts such as total accepted/unavailable/rejected counts, attempt total, channel counts and latest observed/accepted time. These facts stay internal in this slice.

### 5. Existing secured Admin report integration

The existing secured endpoint remains:

`GET /internal/admin/v1/operational-reports/snapshot`

Its response and OpenAPI shape do not change. The internal OTP snapshot influences only existing fields:

- `OTP_DELIVERY_ATTENTION` may be added to `reason_codes` and set the overall signal to `ATTENTION`;
- `OTP_DELIVERY_CRITICAL` may be added and set the overall signal to `CRITICAL`.

Detailed OTP health facts are not exposed over HTTP. This keeps the slice aggregate-only and avoids silently turning the Admin report into a new telemetry API.

### 6. Provider acceptance is not deliverability

`ACCEPTED` means only that the configured provider endpoint returned a successful response. It does not prove:

- mailbox or handset delivery;
- message visibility;
- provider queue completion;
- user receipt;
- successful OTP verification.

Any future delivery receipt, callback or provider-specific status integration requires a separate contract and authenticity model.

## Alternatives rejected

### Log-only observation

Rejected because logs do not provide deterministic restart-durable aggregation in the application contract and may be unavailable to the secured Admin report.

### Store recipient hash or challenge UUID

Rejected because channel-level operational health does not require recipient correlation. Adding it would increase linkability without improving the selected aggregate signal.

### Raise when telemetry persistence fails

Rejected because it could transform an accepted provider call into an API failure and cause clients to retry, producing duplicate OTP sends.

### Expose detailed snapshot immediately over HTTP

Rejected because the existing aggregate reason code is sufficient for the current operator decision. A detailed telemetry endpoint requires its own authorization, retention, pagination and disclosure review.

### Treat quiet as healthy

Rejected. Quiet means there was no observed traffic, not that the provider is healthy. The model therefore uses a distinct `QUIET` state rather than `NOMINAL`.

## Consequences

- OTP provider degradation becomes visible after process restart through the existing secured aggregate report.
- No recipient-level telemetry is introduced.
- Observation failure cannot change delivery semantics or trigger retries.
- Thresholds are deterministic and configurable but are not claimed to be production-tuned.
- Detailed operational facts remain available internally for tests and future explicitly governed surfaces.

## Evidence boundary

CI may prove:

- deterministic signal and reason selection;
- minimum-sample ratio suppression;
- append-only privacy-safe schema;
- retention pruning on write/read;
- PostgreSQL restart durability;
- fail-open observer behavior;
- secured Admin reason-code integration;
- unchanged OpenAPI.

CI does **not** prove:

- real email or SMS deliverability;
- externally validated SLOs;
- production threshold quality;
- paging, incident response or operator acknowledgement;
- telemetry completeness during database failure;
- user receipt or successful OTP verification.
