# ADR-0009 — Editorial-first post-Commit Perspective read model

**Status:** Accepted  
**Date:** 2026-07-27

## Context

KEFE's product loop requires a Perspective stage after Commit, but the current Reason Capture contract deliberately stores user reasons as `PRIVATE`. Social reason visibility, moderation thresholds, ranking methodology, consent and AI summarization remain open product decisions. Exposing private reasons merely to complete the UI loop would violate ADR-0007 and silently close those decisions.

At the same time, the M0 needs an executable Perspective boundary so clients can prove that counter-perspectives are unavailable before Commit and can be presented without turning KEFE into an engagement-first comment feed.

## Decision

- The first Perspective read model uses **editorially authored human perspective items** stored under the immutable CaseVersion content boundary.
- The initial `source_kind` is `EDITORIAL_HUMAN`; this is provenance metadata, not a claim that the text came from another participant.
- Perspective items are linked to a CaseVersion, a QuestionVersion and a structured target value.
- The M0 selection policy is `EDITORIAL_OPPOSITION_V1`: after Commit, select published, moderation-approved editorial items whose target value differs from the viewer's committed `SINGLE_CHOICE` response.
- The endpoint is actor-scoped and Commit-gated. A DRAFT session receives `PERSPECTIVE_COMMIT_REQUIRED`.
- Only items with `publication_state=PUBLISHED`, `moderation_state=ALLOWED` and `source_kind=EDITORIAL_HUMAN` are eligible.
- Selection order uses explicit editorial priority plus deterministic tie-breaking. It does not use likes, engagement, popularity or inferred ideological similarity.
- The query is bounded by a technical safety limit. That limit is not a final product presentation decision.
- `decision.private_reason` is not queried by this read model and remains `PRIVATE` even if its moderation state later becomes `ALLOWED`.
- AI summaries, clustering, persuasion scores, Bridge Score ranking and participant-reason exposure remain deferred.

## Consequences

- KEFE can execute `Commit → Reveal → Perspective` without weakening the private-reason boundary.
- The client can distinguish editorial human perspectives from future participant or AI-derived perspective sources.
- Future participant-reason visibility requires an explicit product/privacy/moderation decision and a separate compatible read model; it cannot be enabled by reusing this endpoint implicitly.
- A future ranking model may replace or extend `EDITORIAL_OPPOSITION_V1`, but must remain versioned and methodologically explicit.
