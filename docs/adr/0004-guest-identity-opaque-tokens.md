# ADR-0004 — Guest identity uses opaque revocable bearer credentials

**Status:** Accepted  
**Date:** 2026-07-27

## Context

KEFE's onboarding promise allows a user to experience the product as a guest before creating an account. The M0 API originally trusted a development-only `X-Actor-Id` header, which is not an authentication boundary and cannot be shipped.

The guest mechanism must preserve the Identity Vault/Core separation, avoid unnecessary PII, work before phone/account verification, support revocation and expiration, and remain independent of an external authentication vendor.

## Decision

- The client first obtains a guest credential from `POST /v1/identity/guest`.
- The server generates a cryptographically random opaque bearer token and a separate random `actor_id`.
- Only the SHA-256 hash of the bearer token is persisted; the raw bearer token is returned once to the client and is not stored server-side.
- Guest actor records contain no phone number, email address or other direct identity attribute.
- Protected Decision API operations derive `actor_id` exclusively from the authenticated bearer credential. Client-supplied actor IDs are not trusted.
- Guest credentials are revocable and expire. The initial TTL default is 30 days and is a typed configuration value subject to Privacy/Product review.
- Mobile clients must eventually store the credential in platform secure storage; ordinary preferences/local storage are not sufficient.
- Account creation/verification will later link or migrate the guest actor through an explicit merge/consent flow rather than changing the semantics of the bearer token in place.
- External auth providers, phone OTP providers and device-integrity providers remain adapters around the Identity capability; they are not domain identities.

## Consequences

- M0 can support real guest ownership without collecting phone/email data.
- Leaked database rows do not directly reveal usable bearer credentials.
- Token revocation is possible without waiting for expiration.
- Every authenticated request requires a token-hash lookup until a measured need justifies an additional cache/session strategy.
- Guest-token issuance must receive rate limiting, abuse controls and device-integrity signals before public beta.
