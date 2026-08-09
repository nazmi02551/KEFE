# ADR-0125 — Live RAW Collective Result fallback for Connected Alpha

Status: Proposed / F4 candidate

Issue: #349

Parent: PR #348 / `53a98b1b554b277d2d85d162cf8ccf9bfe95e050`

## Context

The production PostgreSQL decision path commits real actor decisions durably, but the existing reveal read model only returns a persisted `analytics.result_snapshot` with layer `TRUSTED`. The demo seed provides a fixed TRUSTED snapshot for product review; a newly published CaseVersion without such a snapshot returns `RESULT_NOT_READY` even after users commit decisions.

For the first controlled Connected Alpha, KEFE needs a truthful shared result before F5 introduces a reproducible analytics/projection platform. That bridge must not silently promote raw participation into Signal, Impact, representativeness, truth or normative authority.

A separate audit initially suspected stale Question mapping in the base PostgreSQL adapter. The canonical production inheritance chain already resolves this through `PostgresExploreDecisionRepository`, which maps the current Question schema and immutable CaseVersion fields. No duplicate mapping fix is introduced by this ADR.

## Decision

Keep persisted TRUSTED snapshots authoritative when present.

When no TRUSTED snapshot exists, the PostgreSQL decision repository may derive a live `RAW` Collective Result at reveal-read time from the currently committed population for that exact CaseVersion.

The RAW fallback:

1. selects the first required `SINGLE_CHOICE` question using canonical issue/question order and the latest active QuestionVersion;
2. includes only responses belonging to `COMMITTED` weigh sessions;
3. relies on the existing database invariant allowing at most one committed session per actor + CaseVersion;
4. includes every configured option, including options with zero committed selections;
5. ignores values outside the configured option set;
6. returns option proportions with `n` equal to the counted committed population;
7. returns no snapshot when `n = 0`;
8. uses `layer=RAW` and `confidence=INSUFFICIENT`;
9. is calculated on read and is not persisted in `analytics.result_snapshot` in this slice.

## Why read-time aggregation first

Connected Alpha is deliberately small and starts with one API replica. A background result-projection worker, durable aggregation cursor, retry model and freshness/SLO contract would expand this F4 bridge into F5 analytics infrastructure prematurely.

Read-time aggregation gives the alpha one source of truth — committed PostgreSQL data — with no stale projection risk. F5 may later replace it with precomputed snapshots behind the same reveal contract after performance, methodology and operational evidence exist.

## Privacy and methodology boundary

RAW aggregation must not consume:

- private reason text or reason tags;
- confidence answers;
- demographics or country;
- device information;
- identity/profile attributes;
- trust, bot or social-worth scores.

The result is a count/proportion of observed committed responses. It is not a representative survey, statistical confidence statement, Signal, Impact measurement or judgment about a person/group/country.

## TRUSTED precedence

This slice does not redefine TRUSTED methodology. If a reviewed persisted TRUSTED snapshot exists, the existing reveal behavior remains unchanged and returns it before considering RAW fallback.

This permits product-review/demo fixtures and future methodology-qualified snapshots to coexist with the alpha bridge without silently rewriting their meaning.

## API and mobile impact

No endpoint or response shape changes. `RevealResult.layer` is already represented as a generic string in mobile, so `RAW` requires no alternate UI/runtime branch.

Commit First and Blind First remain intact because aggregation is reachable only through the existing post-Commit reveal path.

## Scaling boundary

The read-time query is accepted only for controlled Connected Alpha scale. Before larger public use, F5 must evaluate query cost, indexing, caching/precomputation, freshness, anomaly controls and methodology-qualified layers.

## Non-claims

This ADR does not establish representative sampling, country/demographic comparison, Signal, Impact, anti-bot weighting, production-scale analytics, deployed SLOs, store readiness, F4 completion or CAP-123 lifecycle promotion.
