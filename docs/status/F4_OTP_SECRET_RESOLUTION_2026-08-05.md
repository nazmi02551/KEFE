# F4 OTP Secret Resolution Checkpoint — 2026-08-05

## Scope

- Foundation wave: F4 identity/privacy/production
- Capability: CAP-084 Guest-to-account conversion and account continuity
- Issue: #326
- Parent runtime: PR #325 exact head `9efd6d894748729944d17188447dcf26d322a3c6`
- Branch: `feature/f4-otp-secret-resolution`
- Candidate exact head: pending final exact-head verification

## Bounded advancement

This slice removes the production HTTP OTP credential from process-lifetime adapter state:

- production requires opaque `KEFE_OTP_HTTP_SECRET_REF` configuration;
- production rejects direct `KEFE_OTP_HTTP_BEARER_TOKEN` configuration;
- the default executable reference is `envref://VARIABLE_NAME`;
- the existing generic `SecretReferenceResolver`, registry and zeroing `SecretLease` model are reused;
- each logical OTP send resolves exactly one bounded lease;
- bounded provider retries reuse the exact request and idempotency key without re-resolution;
- every acquired lease is closed in `finally`;
- the next logical send resolves again and can observe credential rotation without process restart;
- retryable/final resolution failures map to existing generic OTP public errors;
- resolution failure performs zero provider calls;
- secret material, secret reference, recipient, OTP and provider payloads remain outside logs, health events and Admin reports;
- non-production direct `SecretStr` configuration remains an explicit compatibility path;
- the public API, exact OpenAPI and database schema remain unchanged.

## Contract-first evidence

- ADR-0115 — Rotation-safe OTP secret resolution
- `docs/contracts/otp-secret-resolution.v1.json`
- `services/api/tools/check_otp_secret_resolution_contract.py`
- updated parent `check_otp_http_delivery_contract.py`
- memory tests `test_otp_secret_resolution.py`
- updated production composition tests `test_otp_http_delivery.py`
- dedicated `OTP Secret Resolution CI`

## Exact-head evidence

Pending. Do not mark this checkpoint verified until the same final runtime SHA succeeds in:

- OTP Secret Resolution CI — memory and PostgreSQL parent regressions;
- OTP HTTP Delivery CI;
- OTP Delivery Health CI;
- OTP Request Abuse Guard CI;
- API CI — lint, contract sync, unit, exact OpenAPI and PostgreSQL;
- MVP Beta Gates;
- Mobile CI;
- Global Readiness;
- applicable identity/privacy/provider workflows.

## Evidence boundaries

This slice does not prove or provide:

- a connected Vault, KMS or cloud-secret-manager adapter;
- real provider credentials;
- real email or SMS delivery;
- secret-manager access audit logs;
- deployed secret-resolution availability or latency SLOs;
- operator-executed credential rotation or rollback drill;
- provider callback authenticity or delivery receipts.

CAP-084 remains `IMPLEMENTED_PARTIAL`. F4 remains in progress.
