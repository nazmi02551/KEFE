# ADR-0005 — Guest admission rate limiting and provider-neutral device integrity

**Status:** Accepted  
**Date:** 2026-07-27

## Context

Guest onboarding intentionally avoids phone/email collection, which makes credential issuance a high-value abuse surface. KEFE also requires device-integrity signals without coupling Identity domain/application code to Apple, Google or another provider SDK.

## Decision

- Guest credential issuance passes through a dedicated `GuestAdmissionGuard` before an actor/token is created.
- Admission combines an issuance rate-limit signal and a `DeviceIntegrityVerifier` port.
- Source identifiers used by the limiter are hashed before entering the limiter; they remain pseudonymous abuse-control data, not anonymous user data.
- The initial limiter is single-process/in-memory for development and tests. It is **not** a public-beta distributed abuse-control implementation.
- Device integrity has explicit `OFF`, `OPTIONAL`, and `REQUIRED` policy modes.
- An unconfigured provider never reports `VERIFIED`; it reports `UNAVAILABLE`.
- `INVALID` integrity evidence is rejected even when integrity policy is optional.
- `REQUIRED` rejects every result except `VERIFIED`.
- Provider-specific attestation tokens are opaque inputs to the adapter and are not persisted/logged by the admission capability.
- The application does not blindly trust arbitrary forwarded-address headers. Deployment-edge proxy trust must be explicit before production source-address rate limiting.
- Public beta requires a shared/distributed limiter adapter and an approved real device-integrity adapter or documented degraded-mode approval.

## Consequences

- Guest issuance is no longer an entirely unguarded endpoint.
- Apple App Attest / DeviceCheck, Google Play Integrity, or future providers can be added as infrastructure adapters without changing Identity application rules.
- Development can remain usable in `OPTIONAL` mode while production policy can tighten to `REQUIRED` once provider adapters are deployed.
- The current in-memory limiter is a foundation, not a claim of production-grade coordinated abuse prevention.
