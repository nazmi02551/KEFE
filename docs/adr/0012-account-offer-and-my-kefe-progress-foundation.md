# ADR-0012 — Optional Account Offer and My KEFE Progress foundation

**Status:** Accepted  
**Date:** 2026-07-28

## Context

The executable consumer journey now reaches Context, Commit, Trusted Reveal and bounded Perspective. The approved Golden Path continues with an optional post-Reveal Account Offer and My KEFE Progress. This slice must add continuity value without forcing registration, inventing a personality score, introducing streak/XP pressure, or weakening guest privacy.

The current Identity capability issues an opaque, revocable guest bearer credential. Account enrollment factors and verification UX are not yet implemented. Therefore the product may present the value of protecting progress, but it must not expose a fake or non-functional account-creation action.

## Decision

### Placement and guest continuation

- The Account Offer is eligible only after the actor has completed at least one committed Weigh and reached Reveal.
- It is non-blocking, dismissible and must never hide Reveal, Perspective or My KEFE Progress.
- `CONTINUE_AS_GUEST` is always available in this slice.
- No account wall is introduced into onboarding, Explore, Case, Context, Weigh, Commit, Reveal or Perspective.
- Until a real enrollment capability is delivered, the API reports `account_creation_available=false`; clients must not render a create-account button that cannot complete.

### Ownership continuity

- Progress is actor-owned and derived server-side from committed decision records.
- Clients never copy, re-key or merge decision history.
- A future guest-to-account conversion must preserve the same actor identity or execute an audited atomic ownership merge on the server.
- Conversion failure must leave the guest actor and its progress unchanged.
- Raw bearer credentials, private reason text and identity evidence are never returned by the Progress read model.

### Minimum My KEFE Progress model

The first read model is deliberately descriptive and low-claim. It may return:

- meaningful committed Weigh count;
- distinct completed domain count;
- distinct completed Case count;
- first and most recent committed timestamps;
- a bounded list of recently completed Case summaries;
- an `INSUFFICIENT_DATA` / `FORMING` readiness state.

It must not return:

- permanent personality, ideology or political labels;
- psychological or psychometric scores;
- country-representative claims;
- streaks, leaderboards, XP, scarcity pressure or loss-framed nudges;
- private reason text;
- Perspective card text as a claimed user trait.

### Progressive unlock

- `INSUFFICIENT_DATA` is used before three meaningful committed Weighs.
- `FORMING` is used from three committed Weighs onward in this foundation.
- These thresholds control presentation readiness only and are not claimed as validated research thresholds.
- Advanced My KEFE insights require a later methodology-backed contract and may not be inferred locally by clients.

### API boundary

- `GET /v1/me/progress` is authenticated and actor-scoped.
- The response includes `account_offer`, `progress` and methodology metadata.
- The endpoint is a read model; it does not mutate enrollment or onboarding state.
- The response must remain useful for both guest and future account actors.

### Events and analytics

- Progress views may emit `progress.viewed` without returning or logging private response/reason content.
- Account-offer impression/dismissal/continue events may be added only with semantic names and without dark-pattern optimization.
- Conversion metrics must distinguish offer visibility, enrollment availability and completed conversion.

## Consequences

- KEFE can show immediate continuity value after the first decision while preserving optional guest use.
- The mobile client can add a real Progress surface before account enrollment exists.
- The future account capability has an explicit ownership and rollback boundary.
- Rich personal insights remain deferred until sufficient data and methodology exist.
- This ADR does not select phone, email, passkey or another enrollment factor.
