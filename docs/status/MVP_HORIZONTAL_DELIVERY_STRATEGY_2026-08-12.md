# MVP Horizontal Delivery Strategy — 2026-08-12

Status: WORKING DELIVERY RULE / NO CAPABILITY PROMOTION

## Decision

KEFE development will use a **horizontal-first hybrid strategy** until the principal MVP product surfaces are all end-to-end demonstrable.

A feature should normally stop deepening when a real user can reach it, understand it, complete its core journey, and observe a truthful result without fabricated data or a known P0 failure mode. The team then moves to the next missing product value and returns later for production hardening.

## Why this changes the recent pattern

The recent F4 identity/continuity stack required meaningful vertical depth because session expiry could otherwise orphan guest progress, silently change actor identity, or weaken privacy/account boundaries. That depth was justified through the point where the same-actor renewal architecture, transactional guest→account continuity, rotation/replay behavior and candidate HTTP surface existed.

Continuing immediately into every bootstrap path, localization edge case, operational proof and production hardening item would now produce less MVP learning than widening the visible product.

## Default delivery rule

For each major MVP capability:

1. connect it to the canonical user journey;
2. use real repository/runtime data where available;
3. make the core interaction demonstrable on mobile;
4. preserve truthful empty/unavailable states where data/runtime is not ready;
5. cover the highest-value happy path plus destructive/data-loss/security failure boundaries;
6. record deferred hardening explicitly;
7. move horizontally to the next user-visible gap.

## When vertical depth remains mandatory

A short vertical spike may override the horizontal-first rule when stopping early would create a P0/P1 boundary involving:

- authentication/authorization or credential leakage;
- privacy deletion/export or ownership continuity;
- irreversible data loss/corruption;
- methodology integrity or misleading population/psychometric claims;
- destructive moderation/editorial actions;
- payment/legal/compliance boundaries if later introduced;
- a dependency that blocks every other MVP surface.

These spikes should end once the unsafe boundary is controlled; they are not an invitation to production-harden the entire subsystem early.

## Breadth completion target

Before another long hardening sequence, KEFE should present a coherent breadth pass across the main consumer promise:

- Explore/discovery with distinct product experiences visible;
- standard Case → Context → Weigh → Commit → Reveal journey;
- Sports CALL through the same canonical Case engine where SPORTS_CALL content exists;
- Perspective/counter-view and bounded reflection where supported;
- My KEFE/progress and saved/activity continuity;
- account/privacy surfaces at a safe candidate level;
- Atlas represented truthfully without invented country claims until its data/methodology runtime exists.

## Current stop/defer decision

PR #367 session renewal is frozen at candidate depth for this breadth pass. The following remain explicit deferred hardening rather than immediate blockers to horizontal product work:

- legacy access-only continuity bootstrap;
- complete mobile proactive/single-flight renewal orchestration;
- all localized continuity-error states;
- exact OpenAPI regeneration and exact-head CI proof;
- Connected Alpha expiry/renewal operational proof.

They must be completed before the relevant capability is promoted to production-ready status, but not before the next MVP breadth slices are explored.

## First horizontal slice

The first breadth slice is Discovery/Explore:

- expose product experience lanes using existing Case metadata rather than parallel engines;
- make Sports CALL directly discoverable from actual `format=SPORTS_CALL` cases;
- preserve the standard/general Case catalog in the same screen;
- represent Atlas as unavailable/preparing unless a real Atlas read model and methodology-backed data exist;
- do not invent country scores, comparisons or sample data merely to fill the surface.

## Non-goals

This strategy does not lower quality or remove tests. It changes **when** depth is purchased. It does not permit fake data, security shortcuts, silent identity changes, methodology overclaims, or lifecycle promotion without evidence.
