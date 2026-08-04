# ADR-0099 — Canonical Source Brief Candidate Bundle and Explicit Editorial Projection

- Status: Accepted for execution
- Date: 2026-08-04
- Issue: #294
- Parent runtime: PR #293 / `f6076229db05a27367726f4c48e5fc8212f7e96e`
- Foundation wave: F2 — Editorial Projection
- Capabilities: CAP-055, CAP-061, CAP-062, CAP-065, CAP-126

## Context

The canonical runtime now reaches a terminal human-reviewed `SOURCE_BRIEF` Proposal with complete Feed Item, SourceArtifact and immutable evidence lineage. The existing Editorial Projection runtime already maps one terminal `ACCEPTED` `CANDIDATE_CASE` plus accepted dependency Proposals into one Content Authoring `DRAFT`.

The missing bridge is a canonical, explicit operation that creates the review-required Candidate Case bundle. Without it, projection can be exercised only with hand-authored fixtures. A historical `feature/candidate-case-bundle-slice57` branch contains useful bounded stage behavior but is substantially behind the canonical line and cannot be merged wholesale.

## Decision

### Explicit editorial configuration

Candidate bundle creation is not inferred from provider text or Source Brief text. An Admin supplies one immutable, bounded editorial configuration containing:

- slug, title and summary;
- exact base format, primary domain and content-risk codes;
- one issue code/title and one question stable code/prompt;
- bounded single-choice response options;
- exact Flow template code and version;
- content locale, market scope and optional country set;
- fact-bearing and real-event flags;
- required review modes, including `EDITORIAL`;
- context title and optional cultural/legal notes.

The canonical configuration hash covers every field. Any change produces a different seed/run identity and must not mutate an existing bundle.

### Source Brief command

A new API `0.25+` Admin write command is added under the typed Source Brief surface. It requires:

- authenticated Admin write principal;
- valid same-session CSRF;
- `SOURCE_VERIFY` capability;
- exact Source Brief Proposal UUID;
- exact terminal `ACCEPTED` Source Brief review-decision UUID;
- the complete editorial configuration.

The command revalidates:

`SOURCE_BRIEF Proposal → accepted review → normalized Source Brief artifact → accepted FEED_ITEM review → SourceArtifact → immutable evidence reference/hash`.

It creates or reuses one immutable candidate-seed `NormalizedArtifact`, then creates or reuses one separate deterministic ingestion run for `SOURCE_BRIEF_CANDIDATE_BUNDLE / 1.0.0`.

### Deterministic candidate bundle stage

The stage accepts only the exact candidate-seed artifact and exact configuration hash. It revalidates the full Source Brief lineage before emitting exactly three immutable review-required Proposals:

1. `DECISION_PROBLEM`;
2. `QUESTION_DRAFT`;
3. `CANDIDATE_CASE`, depending on the first two.

The three proposals share one bundle risk code and remain `PENDING`. The stage does not create review decisions, materializations, Content Authoring records or consumer content.

Exact replay is idempotent. Existing unequal seed, run, stage or Proposal state is a bounded conflict.

### Explicit Editorial Projection

Editorial Projection remains a separate `CONTENT_PROJECT` operation. It may run only after:

- the exact `CANDIDATE_CASE` Proposal is terminal `ACCEPTED`;
- every dependency referenced by that Candidate Case is present and terminal `ACCEPTED`;
- the exact versioned Flow reference is valid under the selected projection profile.

Projection creates or replays one Content Authoring `DRAFT` and immutable projection lineage. It never submits, reviews, approves, publishes or creates consumer materialization.

### API and persistence

- Candidate bundle command is additive in API `0.25`; API `0.24` and earlier remain unchanged.
- Existing ingestion, Proposal, review, normalized-artifact and Editorial Projection repositories are reused.
- No parallel Candidate Case aggregate, second CMS or duplicate review mutation is introduced.
- Memory and PostgreSQL behavior must remain equivalent.

## Consequences

- Canonical Source Brief lineage can reach the existing Content Authoring DRAFT lifecycle without manual fixture insertion.
- Human editorial choices remain explicit, versioned and reviewable.
- Candidate bundle review and Editorial Projection remain independent actions.
- F2 can advance without introducing AI inference or automatic publishing.

## Rejected alternatives

- Inferring title, dilemma, question, jurisdiction, review modes or Flow from Source Brief text.
- Emitting a directly approved Candidate Case.
- Automatically projecting after Source Brief or Candidate Case acceptance.
- Merging the historical candidate branch wholesale.
- Creating a second Case/CMS lifecycle.

## Non-claims

This ADR does not prove Admin web usability, editorial CQB acceptance, AI-assisted authoring, real provider compliance, production SLO/rollback, publication readiness, store readiness or phone-facing behavior.