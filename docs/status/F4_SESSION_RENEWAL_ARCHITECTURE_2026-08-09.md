# F4 Session Renewal Architecture — 2026-08-09

Status: ARCHITECTURE_CANDIDATE / IMPLEMENTATION_PENDING / EXACT_HEAD_CI_PENDING

Issue: #364  
Parent: PR #363 / `439d771c93ff69b5303bfba0bf761061053920e5`  
Capabilities: CAP-084, CAP-085, CAP-095  
ADR: ADR-0132  
Contract: `docs/contracts/session-renewal-continuity.v1.json`

## Audit finding

The canonical identity runtime has explicit access-token lifecycle states but no renewal capability:

- guest access TTL default: 30 days;
- account access TTL default: 30 days;
- expired/revoked/invalid tokens are rejected distinctly;
- `identity.actor_session` stores current access token hash, expiry and revocation only;
- mobile does not retain exact server expiry or actor kind;
- no refresh/renew endpoint exists.

ADR-0012 requires optional guest continuation and actor-owned progress. Automatically creating a different guest actor after expiry would therefore hide a continuity break rather than recover the user.

## Architecture candidate

ADR-0132 defines:

- same-actor session-family renewal;
- separate opaque access and renewal credentials;
- server-side hash-only storage;
- dedicated HMAC derivation keyring and domain separation;
- monotonic rotation counter;
- previous access/renewal hash slots;
- 60-second response-loss/concurrent retry grace that returns the already-current pair without a second rotation;
- no actor ID in renewal request;
- renewal rejection outside the grace period without new-actor fallback;
- active-access continuity bootstrap for legacy access-only sessions;
- new guest/account issuance returns renewal bundle;
- mobile atomic credential bundle with actor kind + exact access expiry;
- single-flight mobile renewal;
- explicit account reauthentication state on unrecoverable renewal failure;
- guest continuity error state instead of silent orphaning;
- guest→account merge and privacy deletion retire renewal authority with the session.

## Why this is not implemented directly in the privacy PR

The change adds a new credential class, migration, API surface and concurrency semantics. Folding it into PR #363 would mix a bounded privacy bug fix with a security-sensitive identity architecture change and would weaken reviewability.

The architecture is therefore locked separately before runtime implementation.

## Planned vertical implementation

1. actor-session migration + schema snapshot update;
2. token derivation and domain/port model;
3. in-memory renewal contract tests;
4. PostgreSQL row-lock/concurrency/retry behavior;
5. guest issuance/account merge token-bundle responses;
6. renew/bootstrap HTTP API + OpenAPI;
7. atomic mobile credential bundle and legacy migration;
8. single-flight renewal + one-retry access path;
9. merge/privacy revocation regression tests;
10. Connected Alpha expiry/renewal proof.

## Verification state

GitHub Actions currently has no run for parent head `439d771c93ff69b5303bfba0bf761061053920e5`. This architecture checkpoint makes no runtime PASS claim.

No CAP lifecycle status is promoted and no new GitHub Actions workflow is introduced.
