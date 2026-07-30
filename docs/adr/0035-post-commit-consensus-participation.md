# ADR-0035 — Post-commit Consensus participation as the first WE vertical slice

- Status: Accepted
- Date: 2026-07-30
- Tracks: Issue #91
- Extends: ADR-0009, ADR-0019, ADR-0023, ADR-0025
- Depends on: PR #90 / v9 Discovery, Activity and Continuity baseline

## Context

ADR-0019 defines KEFE as a case-agnostic modular decision and public-reasoning engine and establishes the platform lifecycle `ME → WE → SIGNAL → IMPACT`. The current product already has the essential ME path: Context, Decision, Commit, Collective Result, Perspective, DecisionRevision and Reflection. The next meaningful product boundary is a reusable WE capability that lets an actor participate in an explicit community proposition without turning KEFE into a survey engine or contaminating the pre-result decision sample.

A Consensus Card must therefore remain distinct from the original Weigh decision, from Challenge semantics, and from a methodology-qualified Signal. It must preserve Commit First, CaseVersion pinning, actor entitlement, contribution-class separation and the rule that a visible collective pattern does not become legal, electoral, contractual, corporate or normative authority.

## Decision

### 1. Consensus is a reusable post-commit capability

- `CONSENSUS_PARTICIPATION` is a reusable capability over the common Flow/runtime architecture; it is not a Case subtype.
- A Consensus Card has a stable `card_id`; each authored publication has an immutable `card_version_id` and positive `version_no`.
- At most one version of a stable card may be `PUBLISHED` at a time. Participation is pinned to the immutable card version, not merely the stable card identity.
- A Consensus Card version is pinned to the actor's session `case_version_id` and a methodology version.
- The proposition is authored/configured before publication. The mobile client does not invent, summarize or normatively rewrite the proposition at runtime.
- This slice supports zero or more Consensus Cards per CaseVersion; the initial fixtures may expose one card.

### 2. Access is actor-scoped and Commit-gated

- Bearer identity is required.
- The referenced WeighSession must belong to the authenticated actor and be `COMMITTED`.
- Missing or differently owned sessions use the existing non-enumerating `WEIGH_SESSION_NOT_FOUND` boundary.
- Draft/uncommitted sessions return `CONSENSUS_COMMIT_REQUIRED` with HTTP 403.
- Consensus never unlocks before the original decision is committed.

### 3. Contribution classes remain separated

- This first mobile placement is post-Reveal/post-result; therefore every Consensus participation created by this slice is classified `EXPOSED`.
- `EXPOSED` Consensus participation must never be pooled into `CORE_PRE_RESULT` Collective Results or any future core Signal sample.
- The API returns the contribution class explicitly in the read model and participation receipt.
- Future pre-result Consensus experiments require a separate methodology/Flow decision and cannot silently reuse this slice.

### 4. Vote-before-Consensus-result within the card

- An eligible actor may read the proposition and response choices before participating.
- The card's own aggregate distribution and reason-pattern distribution are withheld until that actor has participated.
- This local disclosure gate reduces direct copying of the Consensus distribution even though the actor is already `EXPOSED` to the wider case journey.
- After participation, the actor may read the aggregate for the exact card version.

### 5. Initial response model is bounded

- Initial stance codes are `AGREE`, `MIXED`, `DISAGREE`.
- A card may configure bounded reason tags and a maximum selected-tag count.
- Free text is not accepted in this slice. Existing private Weigh reasons are not copied into Consensus participation.
- One actor has one participation per ConsensusCardVersion. Submission is idempotent; the same idempotency key returns the original receipt.
- Changing a participation requires a future explicit revision model and is out of scope.

### 6. Aggregate is descriptive WE, not Signal

A revealed Consensus aggregate contains only methodology-qualified descriptive fields:

- stable card identity, immutable card-version identity and CaseVersion identity;
- contribution class (`EXPOSED` in this slice);
- sample size;
- stance distribution;
- bounded reason-pattern distribution;
- methodology version;
- generated timestamp;
- provenance/scope note.

The aggregate does not contain demographic segmentation, actor identities, free-text reasons, popularity ranking or persuasion scores.

No `Signal`, Signal score, recommendation, institutional authority or Impact state is created by this slice. Signal qualification remains a separate methodology boundary and must consider the broader factors required by ADR-0019.

### 7. Architecture boundary

- A dedicated Consensus application service owns eligibility, CaseVersion pinning, idempotency and aggregate disclosure.
- A provider-neutral `ConsensusRepository` owns card versions, participation receipts and aggregate reads.
- The Decision repository remains the source of WeighSession ownership/state; Consensus does not duplicate session authority.
- Mobile consumes a dedicated `ConsensusRepository` port with production HTTP and deterministic Product Preview implementations.
- Production must never fall back to Product Preview Consensus data.
- Reusable decision widgets do not start Consensus network work by default; production and Product Preview composition roots explicitly enable the capability.

### 8. Events and privacy

The implementation may emit bounded events such as:

- `consensus.card_viewed`;
- `consensus.participated`;
- `consensus.aggregate_viewed`.

Events may carry stable card/version ids, stance code, contribution class, selected reason-tag codes and bounded counts. They must not contain Case copy, actor profile attributes, original private reason text or any inferred ideology/personality/psychometric label.

## HTTP contract

Initial endpoints:

- `GET /v1/weigh-sessions/{session_id}/consensus-cards`
- `POST /v1/weigh-sessions/{session_id}/consensus-cards/{card_id}/participation`

The GET response exposes stable card identity, immutable card-version identity, card definition and viewer participation state. Aggregate fields are absent/null until participation exists for the viewer.

The POST path resolves the currently published version of the stable `card_id`, requires `Idempotency-Key`, accepts one stance plus bounded reason tags, persists an immutable version-pinned participation, and returns the participation receipt plus now-visible aggregate.

## Acceptance gate

This slice is complete when:

1. machine-readable contract exists and matches this ADR;
2. API models/port/service/in-memory implementation/routes are covered by unit/API tests;
3. stable card identity and immutable card-version identity are distinct and persistence-tested;
4. Commit ownership and contribution-class isolation are tested;
5. idempotent duplicate submission and idempotency-key collision behavior are tested;
6. PostgreSQL migration, seed, persistence, aggregate and outbox behavior pass integration CI;
7. mobile production HTTP repository and deterministic Preview repository share one domain contract;
8. controller covers loading, blocked, eligible, submitting, participated, empty and retryable error states, including multi-card advancement;
9. Consensus UI appears only after the result stage and hides its aggregate before participation;
10. aggregate and reason patterns appear after participation with methodology/provenance copy;
11. production preview-isolation tests pass;
12. existing Commit → Reveal → Perspective → Revision/Reflection flows regress green;
13. API 0.18 generated OpenAPI exactly matches the composed base + additive Consensus overlay contract.

## Deferred

- Signal qualification and scoring;
- CORE_PRE_RESULT Consensus participation;
- demographic/stakeholder segmentation;
- participation revision/change;
- free-text Consensus reasons;
- reactions, comments and social ranking;
- personalized recommendation/targeting;
- institution targeting, Institution Response and Impact;
- legal/electoral/governance authority claims;
- AI-generated Consensus propositions or normative summaries.

## Consequences

- KEFE gains its first explicit WE participation primitive without becoming a generic poll product.
- Commit First and sample integrity remain intact.
- Stable card identity supports future versioning without mutating historical participation.
- The system can later build Signal on reproducible, contribution-class-aware data rather than raw percentages.
- Product Preview can demonstrate the full interaction immediately while production uses the same mobile boundary and API contract.
