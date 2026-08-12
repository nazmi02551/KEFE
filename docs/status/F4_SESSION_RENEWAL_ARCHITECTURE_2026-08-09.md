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

A continuation audit on 2026-08-12 found one material architecture gap in the initial candidate: Issue #364 required a bounded renewal lifetime/inactivity policy, while the first v1.0.0 contract defined rotation/replay behavior but no family horizon.

## Architecture candidate

ADR-0132 and contract v1.0.1 now define:

- same-actor session-family renewal;
- separate opaque access and renewal credentials;
- server-side hash-only storage;
- **180-day absolute continuity lifetime** from family creation;
- **60-day sliding inactivity lifetime** advanced only by successful renewal;
- ordinary bearer/API use does not silently extend continuity;
- successful renewal never extends the absolute deadline;
- guest/account use the same v1 defaults;
- server configuration may tighten defaults but extending them requires contract review;
- `AUTH_SESSION_CONTINUITY_EXPIRED` after either family horizon;
- expired account requires explicit reauthentication;
- expired guest enters continuity error and may start over only through a separate explicit user decision;
- active legacy bootstrap anchors family horizons at bootstrap time and cannot resurrect expired access-only sessions;
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
3. in-memory renewal contract tests, including absolute/inactivity expiry;
4. PostgreSQL row-lock/concurrency/retry behavior;
5. guest issuance/account merge token-bundle responses;
6. renew/bootstrap HTTP API + OpenAPI;
7. atomic mobile credential bundle and legacy migration;
8. single-flight renewal + one-retry access path;
9. merge/privacy revocation regression tests;
10. Connected Alpha expiry/renewal proof.

## Verification state

GitHub Actions currently has no run for parent head `439d771c93ff69b5303bfba0bf761061053920e5`; recent stack PRs also record account-level Actions unavailability. This architecture checkpoint therefore makes no runtime or exact-head PASS claim.

No CAP lifecycle status is promoted and no new GitHub Actions workflow is introduced.
