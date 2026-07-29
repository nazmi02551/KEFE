# ADR-0032 — Descriptive My KEFE Journey Read Model

- Status: Accepted
- Date: 2026-07-29
- Extends: ADR-0012, ADR-0025, ADR-0026, ADR-0030

## Context

KEFE already has an actor-scoped `GET /v1/me/progress` foundation that reports committed Weigh counts, distinct Cases/domains, recent completed Cases and a deliberately low-claim readiness state. The Product Preview currently presents a richer-looking My KEFE screen, but part of that surface is static illustrative data.

DecisionRevision and Reflection are now first-class runtime capabilities. That makes it possible to show a substantially more useful personal history without inferring personality, ideology, psychological traits or causal effects.

The next visible product slice should therefore replace the static My KEFE preview with a repository-backed, server-compatible decision-journey read model. This is a read-model evolution, not a user-profiling subsystem.

## Decision

### 1. My KEFE remains descriptive observed history

My KEFE may summarize only events that KEFE has directly recorded for the current actor, including:

- committed Weighs;
- distinct Cases and domains;
- later committed DecisionRevisions;
- completed Reflections;
- bounded recent decision journeys;
- bounded domain activity based on committed Weigh history.

It must not convert those observations into personality, ideology, political orientation, psychological state, bias diagnosis or other latent-trait labels.

### 2. Existing Progress foundation remains backward compatible

`GET /v1/me/progress` remains the authenticated actor-scoped endpoint.

The existing `account_offer`, `progress` and `methodology` response members remain valid. The richer decision journey is added as an additive `journey` member rather than replacing the foundation or creating a competing source of truth.

Older clients that only consume the existing fields must remain compatible.

### 3. Journey metrics have precise observational semantics

The first journey model may expose:

- `decision_update_count`: count of actor-owned committed DecisionRevisions with `revision_no > 1`;
- `revisited_case_count`: count of actor-owned committed sessions with at least one later DecisionRevision;
- `reflection_completion_count`: count of actor-owned ReflectionCompletions;
- `domain_activity`: committed Weigh counts grouped by Case primary domain;
- `recent_journeys`: a bounded session-level summary of recent committed decision journeys.

A recent journey may contain:

- Case identity/version, title and primary domain;
- initial committed timestamp;
- latest recorded decision timestamp;
- later-decision count;
- whether at least one ReflectionCompletion exists for that session.

These values describe product history only. `decision_update_count` means another committed decision was recorded; it does **not** mean the user's answer necessarily changed.

### 4. DecisionDelta and Exposure remain non-causal and privacy bounded

My KEFE v1 does not expose raw response snapshots, DecisionDelta diffs, private reason text, Exposure metadata or Intervention metadata.

It must not say that an Exposure, counterview or Intervention caused a later decision. Reflection's existing non-causal semantics remain binding.

A future methodology-backed feature may summarize explicitly approved, non-sensitive derived observations, but that requires a separate contract and review.

### 5. Historical compatibility is required

Committed Weigh history predates DecisionRevision/Reflection persistence. Therefore:

- committed `weigh_session` remains authoritative for baseline decision history;
- revision/reflection data enriches the read model when present;
- absence of lineage rows must produce zero/false enrichment, not hide older committed history;
- queries must use actor ownership and left-join semantics where lineage is optional.

No migration/backfill is required for this slice.

### 6. Domain activity is activity, not preference scoring

`domain_activity` may report how many committed Weighs occurred in each domain and the most recent timestamp for that domain.

It must not label a domain as a user's interest, belief, identity, expertise or political preference. Ordering is a presentation decision based on recorded activity only.

### 7. No cross-user comparison in this slice

The first journey read model is strictly self-history. It does not add:

- community similarity scores;
- country/region comparison;
- expert-group similarity;
- ideological clustering;
- recommendation targeting derived from decision history.

Those concerns require separate methodology, privacy and product review.

### 8. Mobile consumes a replaceable repository boundary

The reusable My KEFE surface consumes the existing `ProgressRepository` boundary and typed journey models.

Production uses the HTTP repository. Product Preview may override the same repository with deterministic journey data, but:

- preview data must remain explicitly disclosed as example data;
- production must never import or fall back to the preview repository;
- the My KEFE widget must not contain hard-coded Case-specific behavior;
- the screen must remain usable when journey enrichment is absent or empty.

### 9. Presentation must distinguish counts from claims

The initial UI may show cards such as:

- total committed Weighs;
- revisited decisions;
- completed Reflections;
- domain activity;
- recent decision journeys.

Copy must use observational language such as `yeniden tarttın`, `yansımayı tamamladın`, or `bu alanda X tartım var`. It must not use language such as `fikrin değişmeye yatkın`, `şu görüştesin`, `empatin yüksek`, or `bu içerik seni etkiledi`.

## First implementation slice

The first permitted runtime slice is:

1. extend the existing Progress domain/read model with typed journey summaries;
2. implement memory and PostgreSQL actor-scoped aggregation without schema changes;
3. add the additive `journey` response to `GET /v1/me/progress`;
4. update OpenAPI/contract tests while preserving existing response members;
5. extend Flutter progress models and HTTP parsing;
6. add a deterministic `PreviewProgressRepository` implementing the same contract;
7. replace the static Product Preview My KEFE surface with a shared repository-driven My KEFE journey screen;
8. add API, PostgreSQL and Flutter tests covering historical compatibility, privacy exclusions and preview isolation.

## Deferred

- personality or psychometric models;
- ideology/party inference;
- community/country similarity scoring;
- decision-history-driven targeting;
- causal interpretation of exposures/interventions;
- raw response/reason history;
- longitudinal research claims;
- streaks, XP, leaderboards or scarcity mechanics;
- account enrollment implementation.

## Consequences

- My KEFE becomes visibly useful from recorded product history instead of static illustrative metrics.
- Existing Progress API clients remain compatible.
- DecisionRevision and Reflection gain product value without becoming a profiling engine.
- Historical committed sessions remain visible even when lineage enrichment did not exist at commit time.
- Future deeper personal insight work has a clear boundary requiring methodology and privacy review before implementation.
