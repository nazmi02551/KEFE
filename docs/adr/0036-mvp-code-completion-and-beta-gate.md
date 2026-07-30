# ADR-0036 — Canonical MVP code completion and beta gate

- Status: Accepted
- Date: 2026-07-30
- Tracks: Issue #93
- Extends: ADR-0004, ADR-0008, ADR-0012, ADR-0019, ADR-0034, ADR-0035
- Documentation authority: KEFE Documentation Ecosystem v3.4 / MVP Delivery Plan v1.3.0

## Context

The executable KEFE stack now exceeds a normal MVP in several areas: generic Flow composition, DecisionRevision, Reflection, first-class Claim/Argument persistence, secured Admin foundations, Product Preview, Activity continuity, provider-neutral media, and the first explicit WE / Consensus capability. However, the approved MVP baseline also contains several launch-critical consumer and trust capabilities that are not satisfied merely by having the core decision journey visible.

The repository must not declare the MVP complete while account continuity, explicit sharing, privacy lifecycle, bounded community reasons, local retention, beta catalog readiness, and quality/operations gates remain implicit or absent.

At the same time, human usability testing, editorial acceptance, store policy review, production OTP delivery configuration, and production SLO measurement are external launch gates and cannot honestly be simulated as completed code.

## Decision

### 1. Two completion states

KEFE distinguishes:

1. `MVP_CODE_COMPLETE` — all repository-owned MVP behavior, contracts, persistence, mobile integration and automated gates are implemented and green.
2. `BETA_GATE_PASSED` — external/human release evidence has also passed.

`MVP_CODE_COMPLETE` must never be described as a public/store-ready production release when beta gates remain open.

### 2. Account continuity is optional but functional

- Guest use remains the default and never blocks the Golden Path.
- Account upgrade uses a provider-neutral OTP challenge/delivery boundary.
- A verified challenge can create or resolve an Account Actor and explicitly merge the current Guest Actor into it.
- Merge is server-authoritative, explicit, idempotent and preserves committed history without client-side copying.
- Account identifiers are normalized and stored as non-public authentication identifiers; raw OTP values are never persisted.
- Production OTP delivery remains an adapter/configuration concern. Test/local adapters may expose deterministic delivery evidence only outside production.

### 3. Sharing is explicit and Commit-gated

- A Share is a separate actor command, never an implicit analytics event.
- Share creation requires an actor-owned COMMITTED WeighSession.
- Private reason text, unpublished drafts, private actor/profile fields and pre-Commit collective data are forbidden.
- A share token is opaque, revocable/expiring and resolves to a bounded public read model.
- Sender decision inclusion is explicit; default is Case-only sharing.
- Receiver continuation points to canonical Case identity/version semantics and never bypasses Commit First.

### 4. Community Reason is separate from Private Reason

- Existing private Weigh Reason remains private and is never silently republished.
- A participant may explicitly publish a separate post-Commit Community Reason using bounded configured tags and optional bounded text.
- Publication requires moderation state; unsafe text is never publicly readable while pending/blocked.
- Community read is descriptive and bounded, with stable ordering not driven by popularity.
- Reactions are a small controlled set and do not rank truth, importance or Signal eligibility.
- Reports create moderation input only; they do not automatically determine truth or guilt.
- Basic clustering in MVP means server-derived bounded tag/pattern counts, not AI persuasion/personality inference.

### 5. Privacy lifecycle is executable

- Authenticated actor can request a machine-readable export of actor-scoped product history that is safe to expose to that actor.
- Private Reason is exportable to its owner; credentials, token hashes, internal security telemetry and other actors are not.
- Delete is explicit and server-authoritative.
- Guest deletion removes/revokes actor-linked private state where allowed and anonymizes retained aggregate contributions when integrity/accounting requires retention.
- Account deletion follows the same product-data boundary; legal/audit exceptions must remain explicit.
- Retention metadata is typed and visible in the privacy contract.

### 6. Offline draft retention must match MVP policy

- Uncommitted local decision drafts expire after seven days.
- Persistent mobile draft storage must use an encrypted-at-rest storage boundary rather than plain SharedPreferences JSON.
- Uncertain Commit recovery remains server-authoritative and must never be expired/rewritten in a way that can duplicate or mutate a possibly committed decision.

### 7. Beta content readiness is measurable, not hard-coded runtime logic

- Automated readiness requires at least 20 L0 DILEMMA and 4 L0 CALL publishable catalog fixtures/records across the generic authoring/runtime model.
- No Case-specific screen/controller/runtime class is permitted.
- Automated catalog count is engineering evidence only. Editorial CQB acceptance remains a human beta gate.

### 8. Quality gates

Repository-owned beta evidence includes:

- contract/OpenAPI drift checks;
- API unit + PostgreSQL integration tests;
- Flutter format/analyze/widget tests;
- Commit/Reveal recovery regression tests;
- accessibility semantics + locale/theme smoke tests;
- automated performance budget smoke for critical API paths in CI or a repeatable benchmark harness;
- operational runbook for rollback/kill switches and degraded-provider behavior;
- release checklist that distinguishes automated proof from external approval.

### 9. External/human gates remain explicit

The following cannot be marked passed solely by repository code:

- production OTP delivery credentials/routing and deliverability;
- human phone usability checklist;
- official Apple/Google store compliance review at the release date;
- editorial CQB approval of launch content;
- measured production SLO/load behavior after deployment.

### 10. Scope guard

Signal qualification, Impact lifecycle, research-grade representative estimation, political P2+ content, psychometric/ideological profiling, Rooms/Circle/Live, KEFE+, and full B2B workflows are not required for MVP code completion.

## Acceptance gate

MVP code completion requires all of the following to be green on one exact stacked head:

1. current Golden Path and v9 Discovery/Activity/continuity regression;
2. Account OTP + explicit guest merge contract/runtime/tests;
3. Share create/read/revoke + pre-Commit/privacy tests;
4. Community Reason publish/read/reaction/report + moderation/non-leakage tests;
5. actor privacy export/delete + retention tests;
6. encrypted/expiring local draft adapter + uncertain-Commit recovery tests;
7. beta catalog readiness check >=20 DILEMMA + >=4 CALL;
8. quality/operations/checklist artifacts;
9. API/PostgreSQL/Mobile CI pass;
10. `docs/status/CURRENT.md` records exact code head, remaining external gates and recovery prompt.

Only then may Issue #93 be closed as `MVP_CODE_COMPLETE / BETA_GATE_PENDING`.