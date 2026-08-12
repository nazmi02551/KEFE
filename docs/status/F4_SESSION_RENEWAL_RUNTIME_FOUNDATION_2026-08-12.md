# F4 Session Renewal Runtime Foundation — 2026-08-12

Status: IMPLEMENTATION_PARTIAL / DRAFT / EXACT_HEAD_CI_PENDING

Issue: #364  
Parent architecture: PR #365 / ADR-0132 / `session-renewal-continuity.v1.json` v1.0.1  
Implementation PR: #367  
Capabilities: CAP-084, CAP-085, CAP-095

## Implemented in this checkpoint

- linear migration `20260806_0034 -> 20260812_0035` extends `identity.actor_session` with renewal/previous-pair/rotation/continuity metadata;
- no parallel identity/session table is introduced;
- reviewed runtime defaults are explicit: 30-day access, 60-day sliding inactivity, 180-day non-sliding absolute continuity and 60-second previous-renewal response-loss grace;
- configuration may tighten the reviewed continuity defaults but cannot silently extend them beyond the contract bounds;
- production rejects the development renewal derivation secret;
- deterministic HMAC-SHA256 access/renewal derivation uses separate purpose domains, session family, actor identity and monotonic rotation counter;
- retained derivation keys can reproduce already-current credentials without plaintext server persistence;
- repository contract now exposes renewal resolution and compare-and-swap rotation semantics;
- in-memory identity repository supports current renewal lookup, bounded previous-renewal grace, continuity expiry, revocation, stale-rotation rejection and previous access grace;
- previous access grace is capped by the old access expiry so renewal cannot revive an already-expired bearer credential;
- focused unit tests cover policy/derivation and in-memory renewal CAS/replay behavior.

## Intentionally not exposed yet

No consumer endpoint or issuance response is changed in this checkpoint. In particular:

- `/v1/identity/session/renew` is not exposed yet;
- continuity bootstrap is not exposed yet;
- guest issuance does not yet return a renewal bundle;
- account conversion does not yet return a renewal bundle;
- PostgreSQL renewal lookup/row-lock rotation is not implemented yet;
- mobile atomic credential bundle/single-flight renewal is not implemented yet.

This prevents a half-working security-sensitive API while exact-head execution is unavailable.

## Next implementation boundary

The next slice on PR #367 should converge the same repository contract across PostgreSQL and account conversion before opening HTTP behavior:

1. implement PostgreSQL renewal lookup and atomic rotation using row locking / compare-and-swap semantics;
2. preserve current account merge replay guarantees while attaching a new account session-family renewal pair;
3. update guest issuance to create its session family and renewal pair;
4. add memory + PostgreSQL response-loss/concurrency/revocation tests;
5. only then add renew/bootstrap HTTP, error registry and OpenAPI;
6. follow with mobile atomic bundle and single-flight retry.

## Verification boundary

The isolated agent runtime cannot resolve github.com for a local clone, and recent stack records show GitHub Actions unavailable. Therefore no exact-head test/CI PASS is claimed.

Static repository delta and tests are candidate evidence only. CAP lifecycle status remains unchanged and F4 is not complete.
