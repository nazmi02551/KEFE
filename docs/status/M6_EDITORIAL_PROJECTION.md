# M6 Editorial Projection Checkpoint

**Date:** 2026-07-29  
**Repository:** `nazmi02551/KEFE`  
**Architecture lock:** PR #69 / ADR-0029 — merged after green API CI

This checkpoint supplements `docs/status/CURRENT.md`. The M5 runtime checkpoint remains `docs/status/M5_INGESTION_ORCHESTRATION.md`.

## Locked boundary

ADR-0029 defines the reviewed Candidate Case → Content Authoring DRAFT projection boundary.

Binding decisions:

- `CANDIDATE_CASE` remains an ingestion-orchestration Proposal; it is not a Case, approved CaseVersion or publication state.
- Projection is a separate explicit authenticated editorial/Admin action.
- Source Candidate Case must have terminal `ACCEPTED` review; profile-required dependencies must also be ready/accepted/materialized as contracted.
- A versioned `EditorialProjectionProfile` maps accepted proposal schemas into the existing Content Authoring DRAFT aggregate.
- Hidden/default inference is forbidden. Missing required authoring data fails safely or requires explicit editor input.
- FlowTemplate selection is explicit/versioned; it may not be inferred from title, Domain, Base Format or provider.
- Projection must preserve multiple decision problems/issues, multiple Questions, ordering and typed response schemas.
- Projection is atomic and idempotent: one coherent Content Authoring DRAFT + immutable `EditorialProjectionRecord`, or neither.
- Projection creates DRAFT only. It cannot submit for review, approve, publish, supersede a published CaseVersion or write consumer tables.
- Accepted Claim/Argument/Evidence provenance may be referenced, but projection does not recalculate ClaimAssessment, mutate Claim State, merge claimant identity or remap canonical Claim States into the four-state consumer Context contract.
- Current risk/review policy may make review stricter but may never silently weaken binding high-risk gates.
- A superseding Candidate Case never auto-mutates an existing projected DRAFT or published CaseVersion; another explicit projection/editorial resolution is required.
- Projection contains no provider SDK/crawler/AI call. AI-assisted rewriting must first become a new reviewed Proposal through ADR-0028.

## Contract

- `docs/contracts/editorial-projection.v1.yaml` v1.0.0 — architecture locked, implementation pending at the architecture merge.
- manifest advanced to v1.36.0.
- OpenAPI unchanged because the architecture lock adds no HTTP behavior.

## First permitted implementation slice

- `EditorialProjectionProfile` identity/version;
- explicit idempotent `EditorialProjectionCommand`;
- immutable/durable `EditorialProjectionRecord`;
- ACCEPTED Candidate Case + dependency validation;
- deterministic schema-driven mapping into the existing Content Authoring DRAFT aggregate;
- explicit Flow selection handling with no hidden inference;
- atomic DRAFT + projection-record persistence;
- memory/PostgreSQL coverage;
- architecture fitness proving there is no review/approval/publish shortcut and no provider/AI dependency.

Explicitly excluded:

- automatic projection after proposal acceptance;
- external provider or AI calls;
- automatic Content Authoring review/approval/publication;
- consumer Claim Graph/Context status remapping;
- Admin queue/composer UI;
- bulk projection;
- new runtime Case classes.

## Continuation rule

Before writing the M6 runtime, inspect and reuse the exact existing Content Authoring models/repository/lifecycle and PostgreSQL transaction boundary. Do not create a second CMS or a parallel authoring aggregate. PostgreSQL projection must guarantee atomic draft creation + projection ledger rather than "create draft, then best-effort write ledger".
