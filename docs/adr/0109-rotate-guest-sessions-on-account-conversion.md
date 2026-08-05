# ADR-0109: Rotate guest sessions on account conversion

- **Status:** Accepted
- **Date:** 2026-08-05
- **Foundation phase:** F4
- **Capability:** CAP-084
- **Issue:** #314

## Context

KEFE supports anonymous use before a person verifies an account identifier. Product history must survive a first-time guest promotion and a merge into an already existing account.

The previous implementation also preserved the source guest bearer credential. In memory, promotion left the guest session active. In PostgreSQL, merge-into-existing-account reassigned the guest session to the destination account actor. A copied, leaked or session-fixed guest token could therefore inherit authenticated account access after conversion.

## Decision

A successful guest-to-account conversion is a credential-rotation boundary.

1. Every active session owned by the source guest actor is revoked inside the promotion/merge persistence transaction.
2. Existing sessions already owned by the destination account actor are preserved.
3. Product history and actor-owned controls continue to transfer according to the existing deterministic merge policy.
4. The account continuity service issues a new account bearer only after the promotion/merge succeeds.
5. A retired guest bearer resolves as `REVOKED`, including when the source guest actor has subsequently been marked `DELETED`.
6. Guest bearers are never reassigned or promoted into account bearers.

## Consequences

- Clients must replace the guest credential with the returned account credential immediately after conversion.
- Retrying an API call with the old guest bearer returns `AUTH_TOKEN_REVOKED`.
- Other devices authenticated to the destination account remain signed in when another guest identity merges into that account.
- This closes the session-fixation path without changing the public response schema or losing product history.

## Verification

- Focused in-memory repository coverage proves first promotion, merge-into-existing-account, old-guest revocation and destination-account session preservation.
- MVP memory coverage proves product history remains reachable through the new account credential while the old guest credential is rejected.
- PostgreSQL integration coverage proves both conversion paths, ownership transfer, merge provenance, destination session preservation and zero active sessions on the retired guest actor.

## Remaining CAP-084 work

This ADR does not declare CAP-084 complete. Durable replay/idempotency across verification consumption, broader duplicate-side ownership policies and richer participant-facing conflict explanations remain separate work.