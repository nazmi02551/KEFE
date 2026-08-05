# F4 OTP Request Abuse Guard Checkpoint — 2026-08-05

## Scope

- Foundation wave: F4 identity/privacy/production
- Capability: CAP-084 Guest-to-account conversion and data merge
- Issue: #322
- Parent runtime: PR #321 exact head `1ab0e177b26f60669a94b9e338e1d15b79c9196b`
- Branch: `feature/f4-otp-request-abuse-guard`
- Candidate exact head: pending final exact-head verification

## Bounded advancement

This slice adds a destination-level OTP request abuse guard before provider delivery:

- canonical email/phone normalization precedes the channel-scoped destination hash;
- only channel/hash and operational timestamps/counts are persisted;
- production `AUTO` mode enforces the guard and explicit production `OFF` fails closed;
- development/test `AUTO` remains compatible with existing deterministic fixtures;
- configurable cooldown and rolling-window quota are applied;
- provider delivery failure still consumes the admitted request;
- PostgreSQL guard state and challenge insertion share one transaction;
- concurrent same-key requests converge to one admitted challenge inside cooldown;
- rejected requests roll back the candidate challenge;
- guard state survives application restart;
- existing `AUTH_RATE_LIMITED` returns a generic retryable 429;
- account privacy deletion cascades through the latest OTP challenge foreign key;
- success request/response and OpenAPI remain unchanged.

## Contract-first evidence

- ADR-0113 — Durable OTP Request Abuse Guard
- `docs/contracts/otp-request-abuse-guard.v1.json`
- `services/api/tools/check_otp_request_abuse_guard_contract.py`
- migration `20260805_0031` after `20260805_0030`
- memory tests `test_otp_request_abuse_guard.py`
- PostgreSQL tests `test_otp_request_abuse_guard_postgres.py`
- dedicated `OTP Request Abuse Guard CI`

## Exact-head evidence

Pending. Do not mark this checkpoint verified until the same final runtime SHA succeeds in:

- OTP Request Abuse Guard CI — memory and PostgreSQL;
- API CI — lint, contract sync, unit, exact OpenAPI and PostgreSQL integration;
- MVP Beta Gates;
- Global Readiness;
- Mobile CI;
- applicable parent identity/privacy workflows.

## Evidence boundaries

This slice does not prove or provide:

- IP/device fingerprint or edge abuse protection;
- CAPTCHA, proof-of-work or risk scoring;
- distributed cross-region admission;
- real email/SMS deliverability;
- production provider credentials;
- production-tuned thresholds;
- deployed anti-abuse SLO, alerting or incident response;
- operator-validated rollback.

CAP-084 remains `IMPLEMENTED_PARTIAL` until external provider operation, broader abuse controls, production observability and product-domain merge policies are closed with their own evidence.
