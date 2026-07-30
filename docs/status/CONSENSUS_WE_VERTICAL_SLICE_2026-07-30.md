# KEFE Consensus / WE vertical slice checkpoint — 2026-07-30

## Purpose

This checkpoint records the first explicit `WE` product slice on top of the v9 Discovery, Activity and Continuity baseline. It implements post-commit Consensus participation without changing the original Commit First sample, without creating a Case subtype, and without promoting a new APK.

## Product and methodology boundary

- Capability: `CONSENSUS_PARTICIPATION`.
- Placement: post-Collective-Result / post-commit.
- Eligibility: authenticated actor must own a `COMMITTED` WeighSession.
- Contribution class in this slice: `EXPOSED` only.
- EXPOSED Consensus participation is forbidden from `CORE_PRE_RESULT`, the original Collective Result and direct Signal qualification.
- Card aggregate is hidden until the actor participates in that card.
- Consensus aggregate is descriptive WE data, not a Signal, recommendation, governance authority or Impact state.
- Free-text Consensus reasons are not accepted; bounded reason tags only.
- No ideology/personality/psychometric/causal inference or targeting is introduced.

## Versioned card identity

Consensus now has two explicit identities:

- `card_id`: stable identity for the conceptual Consensus Card;
- `card_version_id`: immutable published version identity.

Each version has a positive `version_no`, is pinned to a CaseVersion and methodology version, and historical participation is pinned to the immutable card version. PostgreSQL enforces one published version per stable card.

## API and persistence

API version: `0.18.0`.

Consumer routes:

- `GET /v1/weigh-sessions/{session_id}/consensus-cards`
- `POST /v1/weigh-sessions/{session_id}/consensus-cards/{card_id}/participation`

Implemented:

- dedicated Consensus bounded context;
- application service and repository port;
- deterministic in-memory implementation;
- PostgreSQL repository;
- linear Alembic revision `20260730_0016` after knowledge revision `20260729_0015`;
- durable card-version and participation tables;
- actor/card-version uniqueness;
- actor/idempotency-key uniqueness;
- race-safe idempotency fallback;
- deterministic `IDEMPOTENCY_KEY_REUSED` handling;
- published-card lookup by stable card identity;
- version-pinned participation receipt;
- contribution-class-aware aggregate query;
- demo card seed;
- privacy-safe lifecycle and aggregate events.

Events:

- `consensus.card_viewed`
- `consensus.participated`
- `consensus.aggregate_viewed`

`consensus.participated` is emitted only for a newly created participation, not for an idempotent replay. Event payloads contain bounded ids/codes/counts and do not contain proposition copy or private Weigh reason text.

## OpenAPI and contract discipline

The stable checked-in OpenAPI base remains `0.17.0` and the additive Consensus API is represented by `openapi-consensus.v0.18.overlay.json`.

CI composes base + overlay into the expected `0.18.0` contract and compares it exactly with generated runtime OpenAPI. The overlay adds five Consensus schemas and two protected routes without copying the full stable contract snapshot.

Consensus contract version: `1.2.0`.
Manifest version: `1.38.0`.

## Mobile architecture

Shared domain boundary:

- `ConsensusCard`
- `ConsensusParticipation`
- `ConsensusAggregate`
- `ConsensusRepository`
- `ConsensusController`

Adapters:

- production: authenticated HTTP;
- Product Preview: deterministic preview repository;
- production preview fallback: forbidden.

The capability is composition-gated. Reusable Decision widgets do not start Consensus network work by default. Production and Product Preview entrypoints explicitly enable the capability and inject their appropriate adapters.

Controller states:

- idle;
- loading;
- blocked;
- eligible;
- submitting;
- participated;
- empty;
- retryable error.

Multiple Consensus Cards are supported. After one card is submitted, per-card stance/reason/idempotency draft state is cleared and the controller advances to the next eligible card.

## Mobile presentation

The first UI is placed after post-commit results/perspectives and before progress continuation.

It provides:

- `WE · ORTAK ZEMİN` identity;
- premium Consensus Card presentation;
- explicit `EXPOSED` integrity badge;
- Agree / Mixed / Disagree stance controls;
- bounded reason tags;
- `Sen de Katıl` action;
- aggregate hidden before participation;
- stance distribution and reason-pattern presentation after participation;
- visible sample size;
- methodology/provenance copy;
- explicit notice that the aggregate is not the core result and is not a Signal.

## Verification

Exact code head before documentation-only reconciliation:

`63e95f53828a5ff0d48bce59ba8467f7d735590e`

API CI run `30507967255` — PASS:

- Ruff lint;
- generated OpenAPI export;
- contract sync;
- Case Flow pinning contract;
- generic Flow runtime contract;
- DecisionRevision lineage contract;
- Reflection runtime contract;
- Claim/Argument ingestion contract;
- Admin HTTP contract;
- API unit tests;
- exact composed OpenAPI drift gate;
- Alembic migration;
- PostgreSQL demo seed;
- PostgreSQL integration tests including Consensus persistence/outbox behavior.

Mobile CI run `30507967257` — PASS:

- formatting;
- Flutter analyze;
- all Flutter tests;
- Product Preview Android build;
- internal artifact upload.

The internal Android artifact from this development branch is CI evidence only. It is not a promoted numbered phone-test build and is not supplied as a new APK.

## Regression coverage

The slice verifies:

- Commit-gated access;
- other-actor non-enumeration;
- aggregate withheld before participation;
- EXPOSED contribution isolation;
- idempotent replay;
- immutable second-participation rejection;
- invalid stance/reason handling;
- stable card id vs immutable card-version id;
- PostgreSQL persistence and outbox event count;
- production/preview isolation;
- post-commit mobile interaction;
- multi-card controller progression;
- existing Decision / Reveal / Perspective / Revision / Reflection mobile regression suite.

## Deferred boundary

This slice intentionally does not implement:

- methodology-qualified Signal generation;
- `CORE_PRE_RESULT` Consensus;
- demographic/stakeholder segmentation;
- participation revision;
- free-text Consensus reasons;
- comments/reactions/social ranking;
- institutional targeting or Institution Response;
- Impact lifecycle;
- AI-generated Consensus propositions.

Those require separate architecture and methodology decisions.
