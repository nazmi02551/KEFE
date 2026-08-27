# F4 Session Renewal Runtime Foundation — 2026-08-12

Status: IMPLEMENTATION_CANDIDATE / CONSUMER_AND_MOBILE_RUNTIME_CANDIDATE / EXACT_HEAD_CI_PENDING

Issue: #364  
Parent architecture: PR #365 / ADR-0132 / `session-renewal-continuity.v1.json` v1.0.1  
Implementation PR: #367  
Convergence branch: `feature/f4-session-renewal-convergence` / PR pending
Capabilities: CAP-084, CAP-085, CAP-095

## Implemented in this checkpoint

- linear migrations `20260806_0034 -> 20260812_0035 -> 20260812_0036` extend the existing identity session and guest-merge replay stores; no parallel identity/session store is introduced;
- reviewed runtime defaults remain 30-day access, 60-day sliding inactivity, 180-day non-sliding absolute continuity and 60-second previous-renewal response-loss grace;
- configuration may tighten continuity defaults but cannot silently extend beyond reviewed bounds;
- production rejects development renewal derivation material;
- deterministic HMAC-SHA256 access/renewal derivation uses separate purpose domains, session family, final actor identity and monotonic rotation counter;
- memory and PostgreSQL identity repositories implement current/previous renewal lookup, continuity/revocation checks and compare-and-swap rotation;
- previous-access grace is capped by the old access expiry, so renewal never revives an already-expired bearer;
- `SessionRenewalService` rotates only the same actor/session family, converges one CAS race and reproduces the already-current pair for bounded response-loss retry;
- renewal honors guest/account access TTL settings independently;
- central error registry 1.24.0 includes `AUTH_RENEWAL_INVALID`, `AUTH_RENEWAL_REPLAYED` and `AUTH_SESSION_CONTINUITY_EXPIRED`;
- new guest creation creates session-family id, rotation-0 access/renewal pair and continuity deadlines atomically;
- guest→account conversion now resolves the final account actor first and then creates renewal-capable account session material inside the same repository transaction;
- guest→existing-account and guest→new-account therefore derive credentials from the correct final actor id;
- `guest_merge_replay` stores immutable initial account-session metadata only; no plaintext token is persisted;
- completed account-conversion replay can reproduce the same initial access/renewal pair while later rotations remain separate;
- guarded and unguarded PostgreSQL account-continuity composition both use the renewal-aware transactional adapter;
- `POST /v1/identity/session/renew` is now exposed as a candidate HTTP surface;
- guest issuance and account merge responses expose additive actor kind, renewal token and rotation counter metadata;
- focused candidate tests cover policy/derivation, memory CAS/replay, renewal service, guest issuance and guest renewal HTTP retry convergence.

## Added by the convergence checkpoint

- PR #367 history is merged after the exact-green horizontal MVP breadth head rather than silently reimplemented or squashed;
- active legacy access can call `POST /v1/identity/session/continuity/bootstrap` and receive a rotation-0 bundle for the same actor/session family;
- bootstrap is compare-and-swap guarded, idempotent during the previous-access grace window and fails closed for expired, revoked or structurally partial sessions;
- memory and PostgreSQL adapters implement the same bootstrap resolution and mutation boundaries;
- PostgreSQL candidate tests cover bootstrap across repository restart and concurrent same-renewal-token convergence;
- the generated MVP OpenAPI overlay includes renewal/bootstrap paths and the additive guest/account credential metadata;
- mobile secure storage now persists one versioned atomic bundle containing actor id, actor kind, access token, exact server expiry, renewal token and rotation counter;
- guest issuance and account conversion parse the complete server bundle before replacing the persisted credential;
- one shared production HTTP client performs 60-second proactive renewal, single-flight convergence and at most one authenticated retry after `AUTH_TOKEN_EXPIRED`;
- legacy access-only storage bootstraps only through active server proof; no expired legacy identity or silent replacement guest is synthesized;
- terminal guest, account and legacy failures map to explicit TR/EN continuity or reauthentication messages;
- Production and Connected Alpha compositions use the renewing client; Preview remains isolated and does not gain connected identity behavior;
- the account-conversion replay keyring is still checked before a renewal-capable credential is reproduced, while legacy v1 verification remains byte-compatible and does not claim a renewal bundle;
- existing privacy deletion checks were migrated from split credential persistence to the atomic bundle without weakening actor-bound deletion confirmation;
- `validate_session_renewal_continuity.py` binds the contract, server, OpenAPI, mobile wiring, localization and tests into the existing API/Mobile workflows; no feature-specific workflow was added.

## Current consumer boundary

Repository runtime scope is implemented as a candidate, but capability acceptance remains incomplete:

- exact-head API CI, Mobile CI, MVP Beta Gates and Global Readiness are pending;
- local PostgreSQL tests require the CI service and are not claimed from a skipped local run;
- Connected Alpha expiry/renewal behavior has not been proven against an externally reachable runtime;
- no production auth provider, deployed SLO, human reauthentication/continuity usability or store-delivered client evidence exists;
- the contract and ADR remain architecture candidates, and no CAP lifecycle record is promoted by this branch.

No silent new-guest fallback has been introduced. Preview fixtures and repositories remain outside Production and Connected Alpha compositions.

## Account conversion invariants now preserved

1. verification is consumed under the existing merge transaction;
2. final target account actor is resolved before session derivation;
3. session-family id and rotation-0 access/renewal material are created for that final actor;
4. the account session and immutable replay metadata are persisted in the same transaction;
5. source guest sessions are retired by the existing merge boundary;
6. replay reproduces only the initial completed conversion credential pair;
7. later account renewal rotation does not mutate or expose a replayed later credential.

## Next implementation boundary

1. publish the convergence branch as a stacked draft PR above the exact-green horizontal MVP breadth head;
2. run API CI, Mobile CI, MVP Beta Gates and Global Readiness on one exact head SHA;
3. repair any exact-head diagnostics without broadening scope;
4. retain the preview APK only if that final exact head is a meaningful green mobile checkpoint;
5. perform Connected Alpha expiry/renewal proof against an externally reachable API before any CAP lifecycle promotion;
6. obtain independent human review and explicit product/governance acceptance before changing CAP-084, CAP-085, CAP-095 or F4 lifecycle status.

## Verification boundary

No exact-head CI PASS is claimed by this document until all required workflow runs are attached to one final head SHA. Local API execution and source validators are development evidence; skipped local PostgreSQL cases and unexecuted local Flutter tests are not PASS evidence.

Human usability, production auth operability, CAP lifecycle promotion and F4 completion remain unclaimed.
