# ADR-0116 — Durable OTP alert candidates and Admin acknowledgement

- Status: Accepted
- Date: 2026-08-06
- Foundation wave: F4
- Capabilities: CAP-123 (primary), CAP-084 (supporting)
- Issue: #328

## Context

ADR-0114 introduced privacy-safe, restart-durable OTP delivery health facts and deterministic `QUIET | NOMINAL | ATTENTION | CRITICAL` snapshots. Those snapshots are useful for an operator who is already looking at the Admin operational report, but they do not leave a durable record that a degraded state was observed and they provide no explicit human acknowledgement boundary.

A naive implementation would create one alert per failed delivery, poll the snapshot, or treat acknowledgement as incident resolution. Each option is misleading or operationally noisy. The repository also has no approved external pager, email, Slack, incident-management or on-call integration.

## Decision

Introduce a bounded OTP delivery **alert candidate** authority derived only from final aggregate OTP delivery health snapshots.

### Candidate eligibility

A candidate is eligible only when the aggregate OTP delivery health signal is `ATTENTION` or `CRITICAL`.

The candidate stores only:

- server-generated candidate UUID;
- aggregate signal;
- sorted canonical health reason codes;
- snapshot and window timestamps;
- aggregate total, accepted, unavailable and rejected counts;
- optional aggregate failure ratio;
- server creation timestamp.

It never stores recipient, destination or destination hash, OTP value or hash, challenge/delivery UUID, account/user/device/session identifier, provider request or response body, credential, secret reference, endpoint or provider request identifier.

### Deduplication and escalation

Candidates use a configurable cooldown and bounded retention.

Within the cooldown:

- an existing candidate with severity equal to or greater than the current snapshot suppresses another candidate;
- an `ATTENTION` candidate does not suppress a later `CRITICAL` snapshot;
- therefore `ATTENTION -> CRITICAL` escalation is recorded immediately;
- repeated `CRITICAL` snapshots are suppressed until the cooldown expires.

No background polling or timer is introduced. Candidate evaluation runs after a final OTP delivery health event is durably appended. An alert-candidate failure is observational only and must never replace provider success/failure semantics or cause another provider send.

### Acknowledgement

Acknowledgement is a separate immutable record keyed by candidate UUID. It contains only:

- candidate UUID;
- server-derived Admin audit actor reference;
- server acknowledgement timestamp;
- server creation timestamp.

There is no free-text note field. Exact replay returns the existing acknowledgement unchanged. Acknowledgement requires:

- authenticated Admin write principal;
- dedicated `OPERATIONAL_ALERT_ACKNOWLEDGE` capability;
- recent step-up;
- same-session CSRF;
- exact candidate-ID confirmation.

Acknowledgement means only “an authorized Admin operator observed this candidate.” It is not remediation, recovery, resolution, incident closure, provider receipt, paging success or SLO evidence.

### Admin surface

Add bounded endpoints under the existing operational-report namespace:

- list recent OTP delivery alert candidates with optional acknowledgement filter;
- acknowledge one exact candidate.

The existing snapshot remains read-only and does not create candidates. Consumer and mobile APIs remain unchanged.

## Persistence

Add linear migration `20260806_0033` after `20260805_0032` with:

- `identity.otp_delivery_alert_candidate`;
- `identity.otp_delivery_alert_acknowledgement`.

Candidate and acknowledgement rows reject direct UPDATE. Bounded retention may delete old candidates and cascade their acknowledgement rows. Candidate admission and acknowledgement are serialized/idempotent in PostgreSQL.

## Consequences

Positive:

- degraded OTP delivery states become restart-durable and operator-visible;
- cooldown prevents one-record-per-failure alert spam;
- escalation remains visible;
- acknowledgement is explicit, authorized and auditable;
- no user identity or OTP material enters operational records;
- no external provider or incident platform is prematurely selected.

Trade-offs:

- there is no automatic recovery or incident lifecycle;
- no candidate is emitted merely because time passes without traffic;
- acknowledgement effectiveness and response time remain human/process questions;
- repository evidence cannot validate production thresholds or on-call behavior.

## Explicit non-claims

This decision does not provide or prove external paging, email/Slack notification, incident creation, automated remediation, provider delivery receipts, real email/SMS deliverability, production threshold quality, deployed alert/SLO behavior, operator response effectiveness or production rollback.