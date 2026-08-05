# ADR-0115 — Rotation-safe OTP secret resolution

- **Status:** Accepted candidate
- **Date:** 2026-08-05
- **Foundation wave:** F4
- **Capabilities:** CAP-084
- **Issue:** #326
- **Parent:** ADR-0112 provider-neutral production OTP delivery

## Context

ADR-0112 introduced a provider-neutral production HTTP OTP adapter. Its first implementation accepted `KEFE_OTP_HTTP_BEARER_TOKEN` as a `SecretStr`, materialized the token while the application was composed and retained it as a long-lived Python string in the delivery adapter.

That boundary redacted normal representations, but it still meant routine credential rotation required process restart and the secret lifetime matched the process lifetime. The repository already has a provider-neutral secret-reference registry and a zeroing `SecretLease`; OTP must reuse that model rather than create a second secret subsystem.

## Decision

Production HTTP OTP delivery uses an opaque `KEFE_OTP_HTTP_SECRET_REF`. Direct `KEFE_OTP_HTTP_BEARER_TOKEN` configuration is forbidden in production and retained only as an explicit non-production compatibility path.

The default executable reference is `envref://VARIABLE_NAME`. The reference is treated as sensitive configuration and is never exposed through application representation, HTTP, operational events or Admin reports. Other allowed opaque reference schemes remain adapter points; this decision does not claim a live Vault, KMS or cloud-secret-manager integration.

For each logical OTP send:

1. resolve exactly one bounded `SecretLease`;
2. construct exactly one provider request from that lease;
3. reuse the exact request and idempotency key for bounded transport retries;
4. close the lease in `finally`, which zeroes its mutable byte storage;
5. resolve again for the next logical send, allowing rotation without process restart.

Secret resolution happens before any provider call. Retryable resolution failure maps to the existing retryable `AUTH_OTP_DELIVERY_UNAVAILABLE`; final, unexpected or invalid-material failure maps to the existing non-retryable `AUTH_OTP_DELIVERY_REJECTED`. Operational observation receives only bounded reason codes. It receives no secret reference, secret material, recipient, OTP value or provider payload.

The public account/OTP API and exact OpenAPI document do not change. No database migration is introduced.

## Consequences

### Positive

- Provider credentials are no longer retained by the production OTP adapter for the process lifetime.
- A rotated environment-backed credential is used on the next logical send without restarting the application.
- Transport retries remain idempotent and do not re-resolve a potentially different secret mid-send.
- Resolution failure cannot accidentally call the provider.
- The existing generic secret lease and resolver contracts remain the single credential boundary.

### Trade-offs

- Python must transiently render an Authorization header string for the HTTP library; the zeroing guarantee applies to the owned lease material, not arbitrary interpreter copies. The adapter does not retain that header beyond the logical send.
- `envref://` is a deployment bridge, not a remote secret manager. Environment access controls and rotation propagation remain deployment responsibilities.
- A real managed-secret adapter and operator rotation drill remain external gates.

## Rejected alternatives

### Retain a startup `SecretStr`

Rejected because it requires restart for rotation and extends credential lifetime to the process lifetime.

### Resolve independently for every transport retry

Rejected because a rotation between retries could change authentication while reusing the same delivery idempotency key and make one logical send nondeterministic.

### Store the secret reference or material in delivery-health events

Rejected because operational diagnosis is aggregate-only and must not become a credential inventory surface.

### Automatically fall back to CAPTURE or another provider

Rejected because it would hide production credential failure and could duplicate OTP delivery.

## Evidence requirements

- machine-readable contract `otp-secret-resolution.v1.json`;
- executable contract checker;
- rotation and lease-closure tests;
- retryable/final resolution failure tests proving zero provider calls;
- parent OTP delivery, abuse-guard, delivery-health, guest-merge and privacy regressions;
- exact OpenAPI equality;
- exact-head CI.

## Evidence boundaries

This ADR does not prove real provider credentials, real email/SMS delivery, a connected managed-secret service, deployed secret-access availability, secret-manager audit logs, or an operator-executed credential rotation/rollback drill.
