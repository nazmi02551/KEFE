# F4 OTP Delivery Alert Candidates Checkpoint — 2026-08-06

## Scope

- Foundation wave: F4 identity/privacy/production
- Primary capability: CAP-123 Operational and service-health visibility
- Supporting capability: CAP-084 Guest-to-account conversion and account continuity
- Issue: #328
- Parent runtime: PR #327 exact head `7f8d1eba1210b85f1f8e4401d8322b369155a1ce`
- Branch: `feature/f4-otp-alert-candidates`
- Candidate exact head: pending final exact-head verification

## Bounded advancement

This slice turns degraded OTP delivery health snapshots into privacy-safe, restart-durable operator candidates:

- candidates are eligible only for `ATTENTION` and `CRITICAL` health signals;
- the source remains aggregate OTP delivery health, not recipient-level delivery data;
- equal or greater recent severity suppresses duplicates inside a configurable cooldown;
- `ATTENTION -> CRITICAL` escalation is recorded immediately;
- repeated `CRITICAL` snapshots are suppressed until cooldown expiry;
- candidate creation happens after a final delivery health event is durably appended;
- candidate persistence failure cannot replace provider success/error or trigger another send;
- candidates and acknowledgements are immutable and restart-durable;
- bounded retention may delete expired candidates and cascade acknowledgements;
- acknowledgement is idempotent and stores only server-derived Admin actor/time;
- no free-text acknowledgement field exists;
- acknowledgement requires dedicated capability, recent step-up and same-session CSRF;
- Publisher remains read-only; Reviewer and Access Admin may acknowledge;
- acknowledgement explicitly does not mean remediation, recovery, resolution or closure;
- consumer/mobile APIs remain unchanged;
- the Admin API change is additive and aggregate-only.

## Privacy boundary

Candidate storage excludes:

- recipient or destination;
- destination hash;
- OTP value or hash;
- challenge/delivery UUID;
- account, user, device or session identifiers;
- provider request/response bodies;
- credentials or secret references;
- provider endpoint or request identifier.

Acknowledgement storage contains only candidate UUID, Admin audit actor reference and server timestamps.

## Contract-first evidence

- ADR-0116 — Durable OTP alert candidates and Admin acknowledgement
- `docs/contracts/otp-delivery-alert-candidates.v1.json`
- linear migration `20260806_0033`
- executable `check_otp_delivery_alert_candidates_contract.py`
- updated composable parent OTP delivery-health checker
- memory cooldown, escalation, privacy and idempotency tests
- secured Admin capability, CSRF, step-up and exact-confirmation tests
- PostgreSQL restart, concurrency, retention, schema and UPDATE-rejection tests
- dedicated `OTP Delivery Alert Candidates CI`

## Exact-head evidence

Pending. Do not mark this checkpoint verified until the same final runtime SHA succeeds in:

- OTP Delivery Alert Candidates CI — memory and PostgreSQL;
- Admin Operational Reports CI — API, Admin UI and PostgreSQL;
- OTP Delivery Health CI;
- OTP HTTP Delivery CI;
- OTP Secret Resolution CI;
- OTP Request Abuse Guard CI;
- API CI — lint, architecture contracts, unit, exact OpenAPI and PostgreSQL;
- MVP Beta Gates;
- Global Readiness;
- applicable identity/privacy/provider workflows.

## Evidence boundaries

This slice does not provide or prove:

- external paging;
- email, SMS or Slack operator notification;
- incident-management integration;
- automated remediation or recovery;
- provider delivery receipts or callback authenticity;
- real email/SMS deliverability;
- production threshold quality;
- deployed alert latency, availability or SLO behavior;
- operator response effectiveness;
- operator-executed incident or rollback drill.

CAP-123 advances but remains partial. CAP-084 remains `IMPLEMENTED_PARTIAL`. F4 remains in progress.
