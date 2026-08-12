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
- production rejects the development renewal derivation secret and retained development material;
- deterministic HMAC-SHA256 access/renewal derivation uses separate purpose domains, session family, actor identity and monotonic rotation counter;
- retained derivation keys can reproduce already-current credentials without plaintext server persistence;
- repository contract exposes typed renewal resolution and compare-and-swap rotation semantics;
- in-memory identity repository supports current renewal lookup, bounded previous-renewal grace, continuity expiry, revocation, stale-rotation rejection and previous-access grace;
- PostgreSQL identity repository implements the same current/previous renewal lookup and atomic CAS rotation boundary;
- previous access grace is capped by the old access expiry so renewal cannot revive an already-expired bearer credential;
- `SessionRenewalService` rotates only the same actor/session family, retries one CAS race, and reproduces the already-current pair for response-loss retry without rotating twice;
- central error registry 1.24.0 includes `AUTH_RENEWAL_INVALID`, `AUTH_RENEWAL_REPLAYED` and `AUTH_SESSION_CONTINUITY_EXPIRED`;
- new guest creation now creates session family id, rotation-0 access/renewal pair and absolute/inactivity deadlines atomically on the server;
- `IdentityService` derives renewal credentials from the validated runtime keyring rather than bypassing production settings with a development fallback;
- existing mobile guest response parsing remains structurally tolerant of additive server fields, but the router still intentionally does not expose the renewal token until OpenAPI/mobile storage are updated together;
- focused test candidates cover policy/derivation, in-memory CAS/replay, service response-loss retry and atomic guest renewal-family issuance.

## Intentionally not exposed yet

The server has renewal-capable guest session state internally, but the consumer contract is not opened yet:

- `/v1/identity/session/renew` is not exposed;
- continuity bootstrap is not exposed;
- `GuestCredentialResponse` does not yet expose renewal metadata;
- account conversion does not yet create/return a renewal-capable account session family;
- mobile still stores access token + actor id separately and synthesizes expiry for an already-persisted credential;
- mobile atomic credential bundle and single-flight renewal remain pending.

This prevents a guest-only or half-working security-sensitive API while account conversion, exact OpenAPI and mobile persistence are not yet converged.

## Account-conversion boundary discovered

The existing guest→account replay transaction determines the target account actor inside the repository transaction. This matters because session-token derivation requires the final target actor id and session-family id.

The next account slice must therefore create deterministic account session material only **after** the target actor is resolved and still **inside the same merge transaction**. Moving derivation outside that transaction would break the existing guest→existing-account path or weaken atomic ownership transfer.

The planned transaction-safe shape is:

1. consume/lock verification and resolve the final account actor;
2. allocate the account session-family id;
3. derive rotation-0 access/renewal material from final account actor + session id via a provider-neutral session-material factory;
4. insert the renewal-capable `identity.actor_session` in the same transaction;
5. persist enough immutable initial session metadata in `guest_merge_replay` to reproduce the completed conversion response safely;
6. retire every guest session family as the current merge transaction already requires;
7. keep later rotated account credentials separate from the immutable conversion replay record.

## Next implementation boundary

1. extend guest-merge replay/model/ports with immutable initial account-session metadata;
2. implement the transaction-safe account session-material factory in memory and PostgreSQL merge repositories;
3. add account conversion renewal/replay/revocation coverage;
4. expose guest/account renewal bundles together with exact OpenAPI and central HTTP contract;
5. add `/v1/identity/session/renew` and active-access legacy bootstrap;
6. migrate mobile to one atomic credential bundle with exact server expiry, actor kind, renewal token and rotation counter;
7. implement single-flight proactive/on-401 renewal without silent new-guest fallback;
8. run exact-head API/Mobile/PostgreSQL core gates once Actions execution is available;
9. perform Connected Alpha expiry/renewal proof before any CAP lifecycle promotion.

## Verification boundary

Recent stack records show GitHub Actions unavailable. The isolated agent runtime also cannot resolve github.com for a clone-based local execution path. Connector readback confirms the branch files, but no exact-head test/CI PASS is claimed.

Static repository delta and test code are candidate evidence only. Human usability, production auth operability, CAP lifecycle promotion and F4 completion remain unclaimed.
