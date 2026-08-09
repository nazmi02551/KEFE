# F4 Live RAW Collective Result — 2026-08-09

Status: IMPLEMENTED_CANDIDATE / EXACT_HEAD_CI_PENDING

Issue: #349

Parent: PR #348 / `53a98b1b554b277d2d85d162cf8ccf9bfe95e050`

## Why this slice exists

The canonical PostgreSQL decision path already persists real commits, but reveal previously required a pre-existing persisted TRUSTED snapshot. The demo fixture's `n=1284` result is intentionally static product-review data and must not be mistaken for a live multi-user aggregate.

A Connected Alpha CaseVersion without a TRUSTED snapshot therefore needed a bounded bridge before the F5 analytics platform exists.

## Audit correction

An initial audit also flagged stale typed Question mapping in the base `PostgresDecisionRepository`. The canonical production repository does not consume that mapping directly: its inheritance chain includes `PostgresExploreDecisionRepository`, which already maps current QuestionVersion fields and immutable CaseVersion metadata correctly. No redundant Question-mapping rewrite is included in this slice.

## Implemented candidate

- new `PostgresLiveRawDecisionRepository` between Explore and private-reason persistence;
- TRUSTED snapshot lookup remains first and unchanged;
- if TRUSTED is absent, select the first required SINGLE_CHOICE question by canonical issue/question order;
- count only responses from COMMITTED sessions for that exact CaseVersion;
- include configured zero-count options;
- exclude unknown option values;
- normalize option counts to proportions;
- return no RAW snapshot when there are zero committed qualifying responses;
- return `layer=RAW`, `confidence=INSUFFICIENT`;
- calculate on read; do not write `analytics.result_snapshot`;
- no API/OpenAPI shape change;
- no schema/migration change.

## PostgreSQL acceptance proof encoded

The focused integration test temporarily removes only the demo TRUSTED snapshot, records two independent guest drafts with different choices, then proves:

1. second actor's uncommitted draft does not enter the result;
2. first commit increments RAW `n` by exactly one;
3. second commit increments RAW `n` by exactly one more;
4. rereading the first actor's reveal sees the same shared `n`;
5. option proportions sum to 1;
6. restoring the TRUSTED fixture restores TRUSTED precedence.

The fixture is restored in `finally` so the test does not intentionally leave the demo methodology state altered.

## Methodology boundary

RAW means only observed committed option proportions in the current KEFE population. It is not:

- a representative survey;
- statistical confidence;
- Signal or Impact;
- country/demographic comparison;
- truth or normative authority;
- a user/group personality or ideology inference.

Private reasons, confidence answers, demographics, country, identity/profile data, device data and trust/bot scores are not inputs.

## Scaling boundary

Read-time aggregation is accepted only as a controlled Connected Alpha bridge. Before broader release, F5 must evaluate precomputation, freshness, indexes/query cost, anomaly controls, segmentation policy, monitoring and methodology-qualified result layers.

## Verification state

GitHub Actions is still producing no workflow runs for the recent Connected Alpha heads, including feature-branch push attempts. Exact-head CI therefore remains pending; no PASS claim is made.

## Non-claims

This slice does not prove production-scale performance, representativeness, Signal/Impact, deployed API reachability, real OTP delivery, store distribution, F4 completion or CAP-123 lifecycle promotion.
