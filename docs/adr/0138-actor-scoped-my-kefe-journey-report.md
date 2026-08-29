# ADR-0138 — Actor-scoped My KEFE journey report

Status: IMPLEMENTATION CANDIDATE  
Date: 2026-08-29  
Issue: #387  
Capability: CAP-120  
Parent: PR #386 / `ea9bcf9ecafd3db3b3654bd4163053427014d6f7`

## Context

My KEFE already exposes an actor-scoped, descriptive progress envelope with
bounded recent Case journeys. The canonical decision stores also retain the
exact occurrence times for the initial Commit, later decision revisions and
Reflection completions. Those facts are currently collapsed into counts and a
latest-decision summary, so a person cannot review their own observed journey
as one chronological report.

The missing surface is a consumer read model, not an analytics score. Building
it from the recently added internal analytics projections would incorrectly
make optional measurement infrastructure the authority for actor-owned product
history. The decision and reflection stores remain the canonical source.

## Decision

The existing authenticated `GET /v1/me/progress` envelope gains an additive
`personal_report` member. It contains a newest-first, maximum-24 list of
`moments` derived only from the authenticated actor's committed sessions:

- `INITIAL_COMMIT` from the committed session time;
- `DECISION_UPDATE` from each immutable decision revision after revision 1;
- `REFLECTION_COMPLETED` from each immutable Reflection completion.

Each moment exposes only its type, Case and CaseVersion identity, governed Case
title and primary domain, occurrence time, and the positive revision number for
`DECISION_UPDATE`. Internal session, revision and completion identifiers may be
used only as deterministic tie-breakers and are not returned.

Memory and PostgreSQL repositories must produce the same ordering and content.
The report is reconstructed on read and adds no migration, duplicated history
table or analytics dependency.

## Mobile experience

My KEFE exposes one localized action into `/my-kefe/report`. The report uses the
existing progress controller/envelope, groups no people, and opens a selected
moment through the canonical `/case/:caseId` route. Loading, retryable error and
empty states remain explicit. Product Preview supplies deterministic example
moments through its existing isolated preview repository so the phone candidate
can be reviewed without becoming a production fallback.

The surface may summarize the already-returned observed counts and date range,
but it must not calculate a score, rank, streak, inferred preference or causal
explanation.

## Privacy and methodology boundary

The report never contains:

- responses, private reasons or DecisionDelta contents;
- Exposure or Intervention metadata;
- actor, session, revision or reflection identifiers;
- inferred motive, personality, ideology, psychometric, bias or morality;
- a claim that a Perspective or Reflection caused a decision update;
- aggregate, cohort, Signal, Impact, quality or normative output.

Actor ownership is enforced by the existing authenticated progress endpoint and
repository predicates. Existing account continuity may preserve ownership;
self-service deletion continues to remove the canonical actor-owned records and
therefore removes report moments without a second erasure path.

## Compatibility

`personal_report` is additive. Mobile treats a missing member as an empty report
for compatibility with older servers, but malformed present moments fail
closed during parsing. Existing progress and journey response semantics are
unchanged.

## Preserved invariants

- Commit First and Blind First;
- immutable published CaseVersion and decision revisions;
- generic Case-agnostic Flow and canonical Case route;
- Product Preview/production isolation;
- My KEFE observed/descriptive-only semantics;
- raw backend values are not changed by display localization.

## Evidence

The executable contract, source validator, memory/PostgreSQL tests, OpenAPI
snapshot, strict Flutter parser and widget/route/accessibility tests bind this
boundary to API CI, Mobile CI, MVP Beta Gates and Global Readiness on one exact
candidate SHA.

## Non-claims

This candidate does not complete or lifecycle-promote CAP-120, Chronicle,
analytics reporting, F5 or production readiness. CI does not prove human
usability, store readiness or deployed behavior.
