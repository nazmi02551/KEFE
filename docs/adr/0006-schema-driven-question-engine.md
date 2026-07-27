# ADR-0006 — Schema-driven question engine and explicit requiredness

**Status:** Accepted  
**Date:** 2026-07-27

## Context

The first M0 Case proved the decision loop with one `SINGLE_CHOICE` question. Product authority already requires multiple interaction types such as choice, scale, confidence, ranking and allocation. Encoding each type directly inside a Case screen or base format would couple content design to client releases and make Question behavior difficult to validate consistently across clients.

Question order also cannot depend on UUID ordering or physical database insertion order.

## Decision

- `QuestionVersion` carries a semantic `response_type` plus a versioned `response_schema`.
- Question requiredness is explicit (`is_required`) rather than inferred from response type or screen position.
- `content.question.sort_order` defines deterministic editorial order within an Issue.
- The backend validates submitted values against the question contract before persistence.
- Commit completeness considers only questions explicitly marked required.
- The mobile client dispatches input rendering by `response_type`; base formats such as DILEMMA do not own widget logic.
- The first implemented typed inputs are `SINGLE_CHOICE` and `CONFIDENCE`.
- Confidence range and step are question data (`min`, `max`, `step`), not global UI constants.
- Confidence is optional in the current demo Case. This does not establish a global rule that Confidence is always optional.
- Unsupported required question types fail closed at the client: they must not be silently skipped to unlock Commit.
- Existing local single-answer drafts are migrated into the response-map model when read.

## Consequences

- New question types can be added behind explicit contracts without rewriting the Case flow.
- Server and client behavior remain aligned around the same response metadata.
- Content editors can control requiredness and presentation order independently of identifiers.
- Future ranking/allocation/scale inputs should extend validation and renderer registries rather than add base-format-specific branches.
- Research-grade question definitions may later require additional schema fields and validation, but must remain versioned with the QuestionVersion seen by the user.
