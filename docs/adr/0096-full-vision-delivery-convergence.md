# ADR-0096 — Full-Vision Delivery Convergence

- Status: Accepted for execution
- Date: 2026-08-04
- Issue: #287
- Capabilities: CAP-126, CAP-095; convergence support for CAP-055, CAP-061, CAP-062, CAP-063, CAP-064, CAP-065, CAP-066, CAP-094 and CAP-123

## Context

KEFE has a verified consumer/mobile review line ending at PR #286 and multiple verified or candidate content/admin lines that diverge after PR #232. The repository handoff file is stale and cannot distinguish the current phone review runtime from later infrastructure candidates. Some candidate branches model the same public-feed/subscription boundary differently and reuse overlapping migration/composition surfaces.

Continuing feature development without convergence would create multiple implicit product runtimes, ambiguous evidence and unsafe merge order. A green workflow on an isolated branch does not make that branch part of the active delivery line.

## Decision

KEFE will maintain one machine-readable delivery registry as the executable source for active runtime, integration candidates, alternatives, superseded lines and external gates.

A line is not canonical merely because:

- its CI is green;
- it has a higher PR number;
- it contains more files;
- an APK was produced;
- it implements a roadmap capability in isolation.

The registry must identify:

1. the common verified ancestor;
2. the exact consumer/mobile review head;
3. every divergent infrastructure candidate considered for integration;
4. capability boundaries owned by each line;
5. evidence state and human/external gates;
6. known overlap or migration conflicts;
7. one deterministic next integration action.

Only one line may be `CANONICAL_INTEGRATION_TARGET` for a capability boundary. Other implementations of the same boundary must be `CANDIDATE`, `ALTERNATIVE`, `SUPERSEDED` or `EXTERNAL_GATE` until explicitly reconciled.

## Initial convergence classification

- PR #286 / `ad825906388371eb9bb36b325abf36a2dd813c5c` is the current exact-head verified **consumer review runtime**.
- PR #232 / `2bb18cd3cc34c2dc6bcb84559948b1231e8e2308` is the common divergence base for the current consumer line and later content candidates.
- PR #264 / `80fbc887f16651949ec36819c440154bcfc278a8` is the preferred first content/admin integration candidate because it advances explicit human Feed Item and Source Brief review without creating a provider activation model.
- PR #273 / `00e1fd5ad8e4818d9a5738b6fdc9cd99bb3124fc` and PR #267 / `e3c8a445ace3a9c4fbc734fa7ebf91e97b7c039e` are competing candidates for the public-feed catalog/subscription/activation boundary. Neither is canonical until their domain, migration and composition overlap is reconciled.

The first runtime integration slice after this governance checkpoint must adopt the PR #264 behavior onto the PR #286 line, preserving the current mobile experience and all parent contracts. It must not merge either public-feed alternative in the same slice.

After that slice, a separate contract-first decision will select one canonical public-feed model and explicitly salvage or retire the other implementation. Overlapping migration identifiers must never be merged as-is.

## Invariants

The convergence program preserves:

- Commit First and applicable Blind First;
- immutable published CaseVersion;
- one case-agnostic composable Flow runtime;
- Preview/production isolation;
- one existing Content Authoring aggregate and lifecycle;
- human review separate from materialization, projection, approval and publication;
- no automatic review, approval or publication;
- My KEFE descriptive-only;
- Collective Result is not automatically Signal;
- accessibility, Reduce Motion and low-end Android as continuous gates;
- exact-head CI evidence separate from human, provider, store, SLO and rollback evidence.

## Consequences

Positive:

- future capabilities advance on one deterministic delivery line;
- alternative implementations become explicit rather than silently cumulative;
- stale continuation records become detectable;
- merge order and evidence claims become machine-checkable;
- the full capability portfolio can progress without parallel runtime families.

Costs:

- some green candidate PRs will be reimplemented or selectively adopted rather than merged wholesale;
- integration work may temporarily add no visible feature;
- public-feed activation work pauses until the competing models are reconciled.

## Non-decisions

This ADR does not:

- promote any roadmap, proposal, test or validation capability;
- declare the full foundation complete;
- authorize a real provider or live feed;
- approve production deployment, stores, Signal/Impact or commercial release;
- infer human usability or editorial acceptance from CI.

## Rollback

This ADR can be superseded only by a later accepted ADR that preserves a single auditable delivery line and explicitly migrates the registry. Deleting the registry or returning to implicit branch selection is not a valid rollback.