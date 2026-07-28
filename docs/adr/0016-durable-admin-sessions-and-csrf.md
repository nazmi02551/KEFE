# ADR-0016 — Durable Admin sessions, server-side revocation and CSRF binding

**Status:** Accepted  
**Date:** 2026-07-28

## Context

ADR-0015 defined a separate Admin security domain, capability-first authorization, mandatory MFA, short-lived sessions and CSRF protection before an Admin HTTP surface can exist. The application now has a secured authoring facade, but it still needs a durable provider-neutral session substrate that future SSO adapters and browser endpoints can use without storing raw bearer credentials.

## Decision

- Admin subjects, role assignments, direct capability grants and sessions are persisted in a dedicated PostgreSQL `admin_security` schema.
- `admin_subject_id` is the stable internal authorization identifier. External SSO/provider identities are resolved by future adapters and are not authorization keys.
- Session tokens and CSRF tokens are generated from cryptographically secure random material. Only SHA-256 digests are stored; raw values are returned once to the trusted session-issuing adapter and are never persisted.
- Issuing an Admin session requires an active subject and an MFA-satisfied timestamp. The database requires MFA assurance on persisted sessions.
- The session resolver loads only active role assignments/direct capability grants and produces the existing provider-neutral `AdminPrincipal`.
- Server-side session revocation takes effect immediately through the resolver.
- Session resolution returns the persisted `last_seen_at`; `AdminSecurityService` evaluates idle expiry before calling `mark_seen`. Successful authentication advances `last_seen_at`, so an expired idle session cannot be revived by the touch itself.
- Step-up is persisted on the Admin session and can be refreshed by a trusted authentication adapter without changing roles or capabilities.
- CSRF verification binds the presented CSRF token to the same opaque Admin session token. A CSRF token from another session is invalid even for the same subject.
- Role and direct-capability persistence does not expose an HTTP access-management API in this slice. Future capability assignment commands must flow through the `ADMIN_ACCESS_MANAGE` security boundary and append access audit.
- No login or Admin HTTP endpoint is introduced by this ADR. It establishes the persistence and cryptographic primitives that the next HTTP slice consumes.

## Consequences

- An IdP/SSO provider can be replaced without rewriting Admin authorization or authoring rules.
- Raw Admin session and CSRF secrets are not database assets.
- Browser Admin endpoints can use opaque cookie sessions plus a bound CSRF header without JavaScript bearer storage.
- Revocation, idle expiry, MFA assurance and step-up state are server-authoritative.
