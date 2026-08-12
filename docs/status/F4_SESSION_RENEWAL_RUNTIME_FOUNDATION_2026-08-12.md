# F4 Session Renewal Runtime Foundation — 2026-08-12

Status: IMPLEMENTATION_PARTIAL / CONSUMER_HTTP_CANDIDATE / MOBILE_PENDING / EXACT_HEAD_CI_PENDING

Issue: #364  
Parent architecture: PR #365 / ADR-0132 / `session-renewal-continuity.v1.json` v1.0.1  
Implementation PR: #367  
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

## Current consumer boundary

Server identity continuity is now candidate-complete enough to expose renewal HTTP, but the full consumer capability is not complete:

- active-access legacy continuity bootstrap is still pending;
- exact OpenAPI snapshot/regeneration is pending;
- mobile still persists access token and actor id separately;
- mobile still synthesizes expiry for an already-persisted credential;
- mobile does not yet persist actor kind, renewal token or rotation counter;
- mobile proactive/single-flight renewal and explicit continuity failure states remain pending.

No silent new-guest fallback has been introduced.

## Account conversion invariants now preserved

1. verification is consumed under the existing merge transaction;
2. final target account actor is resolved before session derivation;
3. session-family id and rotation-0 access/renewal material are created for that final actor;
4. the account session and immutable replay metadata are persisted in the same transaction;
5. source guest sessions are retired by the existing merge boundary;
6. replay reproduces only the initial completed conversion credential pair;
7. later account renewal rotation does not mutate or expose a replayed later credential.

## Next implementation boundary

1. migrate mobile secure storage to one versioned atomic credential bundle containing actor id, actor kind, access token, exact server access expiry, renewal token and rotation counter;
2. migrate legacy access-only mobile state only while the access bearer remains valid; never synthesize a recoverable actor after expiry;
3. add single-flight renewal with proactive skew and one retry after `AUTH_TOKEN_EXPIRED`;
4. add explicit guest continuity-error and account reauthentication-required states with TR/EN copy;
5. implement active-access `/v1/identity/session/continuity/bootstrap` for legacy installed clients;
6. regenerate exact OpenAPI and central contract snapshots;
7. run exact-head API/Mobile/PostgreSQL core gates once Actions execution is available;
8. perform Connected Alpha expiry/renewal proof before any CAP lifecycle promotion.

## Verification boundary

No exact-head CI PASS is claimed. The isolated runtime cannot currently provide clone-based execution, and recent stack records showed unavailable Actions execution. Connector readback verifies repository state only; test files are candidate evidence, not execution evidence.

Human usability, production auth operability, CAP lifecycle promotion and F4 completion remain unclaimed.
