# F4 OTP Delivery Health Checkpoint — 2026-08-05

## Scope

- Foundation wave: F4 identity/privacy/production
- Capabilities: CAP-084 Guest-to-account conversion and CAP-123 Admin operational reports
- Issue: #324
- Parent runtime: PR #323 exact head `5257cc17a67474c6ef6ccae91ddbac0e175a015f`
- Branch: `feature/f4-otp-delivery-health`
- Candidate exact head: pending final exact-head verification

## Bounded advancement

This slice converts final provider-neutral HTTP OTP outcomes into a privacy-safe operational health signal:

- `ACCEPTED`, `UNAVAILABLE` and `REJECTED` final results are observed;
- only channel, outcome, attempts, bounded status/error code and time are retained;
- recipient, destination hash, OTP code, challenge/delivery identity, provider payload, credential and endpoint are excluded;
- PostgreSQL events are append-only except retention deletion and have no identity foreign keys;
- default retention is seven days, pruned on event append and snapshot read;
- a 15-minute policy window derives `QUIET`, `NOMINAL`, `ATTENTION` or `CRITICAL`;
- failure ratios are suppressed below a minimum sample size;
- observation persistence failure is fail-open relative to provider semantics and cannot trigger a duplicate send;
- the existing secured Admin operational report receives only aggregate `OTP_DELIVERY_ATTENTION` or `OTP_DELIVERY_CRITICAL` reasons;
- detailed OTP facts remain internal;
- the Admin HTTP response and OpenAPI shape remain unchanged.

## Contract-first evidence

- ADR-0114 — Durable OTP Delivery Health Signal
- `docs/contracts/otp-delivery-health.v1.json`
- `services/api/tools/check_otp_delivery_health_contract.py`
- migration `20260805_0032` after `20260805_0031`
- memory tests `test_otp_delivery_health.py`
- PostgreSQL tests `test_otp_delivery_health_postgres.py`
- dedicated `OTP Delivery Health CI`

## Exact-head evidence

Pending. Do not mark this checkpoint verified until the same final runtime SHA succeeds in:

- OTP Delivery Health CI — memory and PostgreSQL;
- OTP HTTP Delivery CI;
- OTP Request Abuse Guard CI;
- API CI — lint, contract sync, unit, exact OpenAPI and PostgreSQL;
- MVP Beta Gates;
- Global Readiness;
- applicable identity/privacy/provider workflows.

## Evidence boundaries

This slice does not prove or provide:

- real email or SMS deliverability;
- provider acceptance as user receipt;
- externally validated SLOs;
- production threshold tuning;
- paging, alert acknowledgement or incident response;
- operator-executed rollback;
- telemetry completeness during database failure;
- recipient-level diagnosis;
- provider callback authenticity or delivery receipts.

CAP-084 remains `IMPLEMENTED_PARTIAL`. CAP-123 advances through one new secured aggregate reason source but is not complete.
