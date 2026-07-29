# ADR-0029 — Reviewed Candidate → Content Authoring DRAFT Projection

- Status: Accepted
- Date: 2026-07-29
- Depends on: ADR-0013, ADR-0018, ADR-0019, ADR-0022, ADR-0027, ADR-0028

## Context

ADR-0027 made Claims/Arguments first-class and ADR-0028 made ingestion/extraction output reviewable, immutable Proposals. The M5 runtime can now produce, review and durably track proposal kinds such as `DECISION_PROBLEM`, `QUESTION_DRAFT` and `CANDIDATE_CASE` without bypassing editorial governance.

The next missing boundary is the handoff into KEFE's existing Content Authoring lifecycle.

The approved product and editorial documents require that:

- one source may yield multiple Claims, decision problems and Candidate Cases;
- AI/provider output remains a proposal, not editorial acceptance or publication;
- real-event and high-risk content remains behind human review;
- published CaseVersion is immutable and publication pins effective configuration + resolved Flow;
- editorial mutable state never reaches consumer tables before publication;
- the existing DRAFT → IN_REVIEW → APPROVED → PUBLISHED lifecycle remains authoritative.

Without an explicit projection contract, an accepted Candidate Case could be confused with a Case, orchestration could start writing authoring records directly, or retries could create duplicate drafts.

## Decision

### 1. Candidate Case is not Case

`CANDIDATE_CASE`, `DECISION_PROBLEM` and `QUESTION_DRAFT` remain orchestration Proposal kinds. Their acceptance means "editorially eligible for handoff", not "published", "approved Case", or "consumer visible".

`Case`, `CaseVersion`, `Issue`, `Question` and their lifecycle remain owned by the existing Content Authoring bounded context.

### 2. Projection is an explicit Admin/editorial command

Projection occurs only through an explicit authenticated editorial/Admin action using the same server-derived Admin identity/capability boundary already required for Content Authoring.

No source adapter, processor, AI task, ingestion worker or proposal review action may implicitly trigger projection.

### 3. Projection requires an ACCEPTED Candidate Case proposal

The source `CANDIDATE_CASE` must have exactly one terminal `ACCEPTED` ProposalReviewDecision.

Any referenced `DECISION_PROBLEM`, `QUESTION_DRAFT`, Claim/Argument or evidence proposal required by the candidate must also be in the state required by the projection profile. Missing, rejected or changes-requested dependencies fail projection safely.

Accepted proposal status does not bypass existing authoring validation.

### 4. Projection is profile-versioned and schema-driven

A versioned `EditorialProjectionProfile` defines how accepted proposal payload schemas map into existing Content Authoring DRAFT fields.

A projection profile may define mappings for:

- title/summary/locale;
- Domain/Topic/Base Format/Modifier selections;
- risk/editorial review mode proposal;
- Issue/decision-problem structure;
- Question draft structure and response schema;
- source/Claim/Argument provenance references;
- FlowTemplate selection when explicitly present and permitted.

The projection layer must not infer undocumented defaults merely to make a draft valid. Required authoring data that is absent or incompatible causes an explicit projection failure or editor-supplied projection input, never silent guessing.

### 5. Flow selection stays explicit

Projection must not choose a FlowTemplateVersion based on Case title, Base Format, Domain or provider identity.

When Flow selection is carried by an accepted candidate, it must be explicit and versioned. When it is not present, the projection command must either receive an explicit editorial Flow selection allowed by the profile or fail as incomplete.

Publication-time Flow/configuration validation and pinning remain governed by ADR-0022 and the current Content Authoring contract.

### 6. Projection is atomic and idempotent

A successful projection creates one coherent Content Authoring DRAFT aggregate and a durable `EditorialProjectionRecord` linking:

- accepted Candidate Case proposal id;
- terminal review decision id;
- projection profile code/version;
- triggering Admin/editorial identity;
- target Authoring Case id;
- target Authoring CaseVersion id;
- created timestamp;
- provenance/input hash.

The same accepted Candidate Case proposal cannot create multiple logical authoring drafts through retry/replay.

Partial authoring creation is forbidden. Projection either creates the complete DRAFT aggregate + projection record or creates neither.

### 7. Projection never advances authoring lifecycle automatically

Projection may create only DRAFT authoring state.

It may not automatically:

- submit for review;
- approve;
- publish;
- supersede a published CaseVersion;
- materialize into consumer Case/Question tables.

All later lifecycle transitions use existing Content Authoring services, validation, audit and role separation.

### 8. Accepted knowledge provenance is referenced, not rewritten

Where the candidate uses accepted Claim/Argument/Evidence records, projection carries stable references/provenance into authoring metadata/presentation inputs supported by the projection profile.

Projection does not:

- recalculate ClaimAssessment;
- change Claim State;
- merge claimant identity;
- remap canonical Claim States into the four-state consumer Context presentation contract.

A separate Context projection contract remains required before canonical Claim knowledge can alter consumer Context state labels.

### 9. Question and decision-problem structure is preserved

One Candidate Case may include multiple decision problems/issues and multiple Question drafts.

Projection must preserve explicit ordering, identifiers within the candidate bundle and typed response schemas. It must not collapse a multi-question candidate into the legacy single-answer shape.

Question validation remains schema-driven under the existing question engine and Content Authoring rules.

### 10. Risk and review requirements can only become stricter

Projection preserves risk provenance and any mandatory review requirements from the accepted candidate/editorial policy.

Projection may raise the effective authoring review requirement when current policy demands it, but it may not silently downgrade binding high-risk/maker-checker/trust/legal/civic requirements.

The existing publication authority remains the final gate.

### 11. Superseding proposals do not mutate projected drafts automatically

A later Candidate Case proposal that supersedes a previously projected proposal does not mutate the existing Authoring DRAFT and can never mutate a published CaseVersion.

A new explicit projection action is required. If existing Content Authoring invariants prevent a second DRAFT/revision for the target Case, projection fails with a conflict and requires explicit editorial resolution rather than overwriting state.

### 12. Projection failures are durable operational outcomes

Projection distinguishes at minimum:

- source proposal not accepted;
- dependency not accepted/materialized as required;
- projection profile/schema incompatible;
- required authoring field missing;
- invalid taxonomy/configuration/Flow reference;
- authoring lifecycle conflict;
- persistence/concurrency failure.

Retries must reuse the same idempotency identity. A failed projection does not alter the proposal review decision.

### 13. No provider or AI dependency enters the projection domain

Editorial projection consumes accepted provider-neutral proposal records. It contains no source-provider SDK, crawler logic, AI model call, prompt execution or provider credential.

If an editor requests AI-assisted rewriting before projection, that produces a new reviewed Proposal through ADR-0028; projection itself stays deterministic from accepted input + explicit editorial parameters.

## First implementation slice

The first executable ADR-0029 slice should implement:

1. `EditorialProjectionProfile` identity/version contract;
2. `EditorialProjectionCommand` with explicit idempotency key and editorial inputs;
3. `EditorialProjectionRecord` persistence;
4. validation that source Candidate Case and required dependencies are ACCEPTED;
5. deterministic mapping into the existing Content Authoring DRAFT aggregate;
6. atomic DRAFT creation + projection record;
7. in-memory and PostgreSQL adapters/tests;
8. architecture fitness verifying no review/approve/publish shortcut and no provider/AI dependency.

The first implementation slice does **not** include:

- external provider/AI calls;
- automatic projection after proposal acceptance;
- automatic authoring review/approval/publication;
- consumer Claim Graph or Context status remapping;
- Admin queue/composer UI;
- bulk projection;
- new Case runtime classes.

## Consequences

- TODAY/Radar/KEFE’ye Koy can eventually feed the same authoring system without becoming a second CMS.
- accepted candidates become reproducible authoring inputs while editorial authors retain control.
- retries cannot duplicate drafts.
- published historical Cases remain immutable.
- Flow and taxonomy semantics remain configuration-driven rather than inferred from content labels.

## Rejected alternatives

### Treat ACCEPTED Candidate Case as a Case

Rejected. Proposal acceptance is not authoring approval/publication.

### Let orchestration directly insert consumer Case/Question records

Rejected. It bypasses Content Authoring, publication validation and immutable CaseVersion provenance.

### Auto-project immediately when a proposal is accepted

Rejected. Projection is a separate explicit editorial action and may require editor-supplied fields/Flow selection.

### Guess missing Domain/Base Format/Flow from AI or candidate text

Rejected. Schema before Screen and explicit versioned configuration remain binding.

### Update an existing projected DRAFT whenever the proposal changes

Rejected. It destroys reproducibility and can silently overwrite human editorial work.
