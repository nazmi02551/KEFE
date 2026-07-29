# ADR-0028 — Provider-Neutral Ingestion Orchestration and Reviewed Proposal Boundary

- Status: Accepted
- Date: 2026-07-29
- Depends on: ADR-0013, ADR-0019, ADR-0027

## Context

ADR-0027 established first-class Claim/Argument knowledge records and provider-neutral `SourceArtifact` / `NormalizedArtifact` persistence. That foundation intentionally stops before orchestration.

The approved KEFE documentation requires a durable path from current-world signals and submitted sources to human-governed editorial candidates:

- Radar pipeline: Sources → Ingest → Trend Detection → Event Clustering → Deduplication → KEFE-Worthiness → Fact Check → Risk Score → Issue Extraction → Question Proposal → Editorial Review → Publication.
- Editorial pipeline: Signal → Event candidate → Dedup → Acceptance Test → Source/Claim map → Risk → Issue extraction → Question proposal → Localization → Review → Publish → Update/Correction.
- generalized source ingestion: one source may produce 0..N Claims, decision problems and Candidate Cases.
- AI tasks may extract/classify/normalize/suggest/compose/detect, but AI output is a proposal; editorial acceptance is a separate auditable decision.
- AI execution must retain model/prompt/config lineage, hashes, confidence, review state and human oversight.
- provider SDKs must remain behind adapters; malicious URLs/content are untrusted input.
- queues/retries must be bounded; external calls require timeout, retry/backoff/jitter and circuit breaker behavior.
- high-risk publication always remains behind the existing human-governed Content Authoring workflow.

Without a dedicated orchestration boundary, provider adapters or AI task results would be tempted to write directly into canonical Claim/Argument records or Content Authoring drafts, collapsing proposal, review and publication into one unsafe operation.

## Decision

### 1. Orchestration is a separate bounded context

A new ingestion-orchestration bounded context coordinates processing but does not own canonical Claim/Argument truth records or published CaseVersion state.

Its responsibilities are limited to:

- durable ingestion runs;
- versioned stage execution;
- immutable proposal output;
- append-only review decisions;
- idempotent materialization/handoff records;
- execution/provenance references;
- bounded retry/failure semantics.

The existing `knowledge` bounded context remains the system of record for accepted Claim/Argument records. Existing Content Authoring remains the only Case draft/review/publish authority.

### 2. Provider-specific data stops at `SourceAdapter`

An orchestration run accepts references to canonical `SourceArtifact` and, when available, `NormalizedArtifact` records. Provider SDK objects, credentials, request signatures and provider-specific payload classes never enter the orchestration or knowledge domain contracts.

Source acquisition must use only technically, legally and service-terms-permitted access methods.

External URLs/content are untrusted input. Fetching/parsing adapters must apply URL/network policy, timeout, size limits, content-type validation and sandbox/allowlist controls appropriate to the provider.

### 3. Pipeline and stages are versioned configuration, not a closed hard-coded workflow

`IngestionPipelineVersion` identifies a versioned sequence/graph of stage definitions. Stage codes are registry-governed and extensible; a new source type or editorial pattern must not require a new orchestration class family.

The canonical documentation supplies initial stage families such as:

- NORMALIZE
- TREND_DETECTION
- EVENT_CLUSTERING
- DEDUPLICATION
- KEFE_WORTHINESS
- CLAIM_EXTRACTION
- EVIDENCE_MAPPING
- REPLY_ARGUMENT_EXTRACTION
- FACT_CHECK_ASSIST
- RISK_PROPOSAL
- DECISION_PROBLEM_PROPOSAL
- QUESTION_PROPOSAL
- CANDIDATE_CASE_COMPOSITION
- LOCALIZATION_PROPOSAL

This list is not a permanently closed enum. Pipeline/version configuration decides which stages apply to a particular source/risk/editorial path.

### 4. `IngestionRun` is durable and replay-safe

A run is pinned to:

- input artifact identity + content hash;
- pipeline code + version;
- configuration snapshot/hash;
- taxonomy/methodology versions when relevant;
- locale/jurisdiction scope when relevant.

The same deterministic run key must not create duplicate logical runs. A changed source content hash, pipeline version or material configuration creates a new run instead of silently reinterpreting an old run.

Initial run states are:

- QUEUED
- RUNNING
- SUCCEEDED
- FAILED_RETRYABLE
- FAILED_FINAL
- CANCELED

A successful run may end with zero proposals. Human review is not represented as a run waiting state; proposal review has its own durable lifecycle.

### 5. Stage execution is independently auditable

Each stage attempt records at minimum:

- run identity;
- stage code/version;
- attempt number;
- input hash;
- output hash when produced;
- executor kind;
- started/completed timestamps;
- outcome/error code;
- execution/provenance reference.

A stage may be deterministic, AI-assisted or another approved processor behind a port. Domain code does not know a provider name.

Retries are bounded. Infinite queueing or infinite retry is forbidden.

### 6. Semantic output is an immutable `Proposal`, not a direct write

A stage produces zero or more immutable proposals. A proposal contains:

- proposal kind;
- payload schema reference/version;
- payload + payload hash;
- source run/stage lineage;
- taxonomy/configuration/methodology provenance;
- optional confidence/risk metadata;
- optional AI execution reference;
- optional `supersedes_proposal_id` for revised proposals.

Initial proposal kinds may include:

- EVENT_CANDIDATE
- CLAIM
- CLAIM_ASSESSMENT
- EVIDENCE_LINK
- ARGUMENT
- ARGUMENT_RELATION
- DECISION_PROBLEM
- QUESTION_DRAFT
- RISK_ASSESSMENT
- CANDIDATE_CASE

Proposal-kind registry is versioned/extensible. A proposal is never consumer-visible truth merely because it exists.

### 7. Review decisions are append-only and separate from proposals

Human/editorial review creates an immutable `ProposalReviewDecision` rather than mutating proposal content.

Initial decisions are:

- ACCEPTED
- REJECTED
- CHANGES_REQUESTED

A changed proposal is a new proposal revision linked by `supersedes_proposal_id`; old proposal and review history remain intact.

Every review decision records reviewer identity from the authenticated Admin/security boundary, decision time, rationale/reason code where required and applicable policy/risk version.

AI/provider output may never create an ACCEPTED review decision for itself.

### 8. AI execution lineage is explicit and never the system of record

AI capabilities are called through provider-neutral task ports and the AI Orchestrator. Provider/model selection remains outside domain semantics.

Every material AI-assisted proposal must be reproducible/auditable with the available lineage fields:

- capability/task code;
- provider/model/version;
- prompt template/version;
- configuration/taxonomy version;
- input/output hash;
- confidence;
- safety/fallback metadata;
- timestamp;
- execution outcome.

Provider confidence is not truth probability. AI execution output does not directly write Claim State, Case publication state or KEFE normative judgment.

### 9. Accepted knowledge proposals materialize through an idempotent application boundary

For proposal kinds already owned by the `knowledge` bounded context, an ACCEPTED review decision may trigger a separate idempotent materialization command.

Materialization records source proposal id, target kind/id and timestamp. The same accepted proposal cannot create duplicate canonical records on retry.

Materialization failure does not erase the human review decision; it becomes retryable operational work. Review decision and materialization/audit/outbox effects must be transactionally consistent at their own boundary.

`EvidenceLink` materialization never creates/changes ClaimAssessment automatically. `ClaimAssertion` never changes Claim State automatically. Existing ADR-0027 invariants remain binding.

### 10. Candidate Case acceptance does not publish and does not yet create an authoring draft

`DECISION_PROBLEM`, `QUESTION_DRAFT` and `CANDIDATE_CASE` proposals may be reviewed and accepted in this bounded context, but ADR-0028 does not define their mapping into `AuthoringCaseVersion`.

Accepted Candidate Cases remain upstream editorial candidates until a separate editorial-projection contract defines how they become Content Authoring DRAFT objects.

No proposal or orchestration run may call publish directly. Existing DRAFT → IN_REVIEW → APPROVED → PUBLISHED authoring remains authoritative.

### 11. High-risk and factual classifications preserve mandatory human gates

At minimum:

- AI-derived ClaimAssessment proposals require editorial/human acceptance before materialization;
- high-risk real-event question/candidate proposals require human review;
- high-risk publication remains subject to the existing maker-checker/trust/legal/civic gates.

Risk policy may require more review, never less than the approved baseline.

### 12. Queue UX is a derived operational read model

Admin queue concerns such as assignment, saved views, priority and SLA indicators may be built from run/proposal/review state, but queue ordering is not semantic truth and does not mutate proposal history.

Bulk acceptance is not introduced by this ADR.

### 13. Resilience and backpressure are explicit

Orchestration must support:

- bounded queue/concurrency;
- bounded retry;
- timeout;
- exponential backoff + jitter for external calls;
- circuit breaker/fallback where an external capability is used;
- retryable vs final error classification;
- dead-letter/operational inspection for exhausted asynchronous work;
- trace/correlation identifiers without PII.

AI/provider outages must not break the consumer Weigh/Commit/Reveal core loop.

### 14. Privacy, provenance and correction are preserved

Minimum necessary source/claimant metadata is stored. Raw PII is not copied into AI execution logs.

Source changes produce new artifact/run lineage. Accepted proposal corrections append new proposal/review/materialization history; published CaseVersions remain immutable and continue to use the existing correction/new-version workflow.

No ingestion or proposal activity may be used for personality, ideology or psychometric inference.

## First implementation slice

The first executable ADR-0028 slice should implement infrastructure without external providers:

1. `IngestionRun`, `StageExecution`, `Proposal`, `ProposalReviewDecision` and `ProposalMaterialization` domain models;
2. version-pinned pipeline/stage identifiers and replay/idempotency keys;
3. provider-neutral orchestration/task/repository ports;
4. in-memory + PostgreSQL persistence;
5. bounded retry/error-state invariants;
6. deterministic/fake processors for tests only;
7. idempotent materialization for proposal kinds already represented in the knowledge bounded context;
8. contract/fitness + unit + PostgreSQL integration tests.

The first implementation slice does **not** include:

- external source provider SDK/crawler calls;
- AI provider calls;
- consumer ingestion or Claim Graph UI;
- Candidate Case → Content Authoring DRAFT projection;
- automatic Case publication;
- Context Claim-status remapping;
- graph database;
- Admin queue UI.

## Consequences

- Radar/TODAY and KEFE’ye Koy can share one orchestration boundary without provider-specific domain branches.
- AI can accelerate extraction/composition while human/editorial acceptance remains explicit and auditable.
- retries/reprocessing cannot silently duplicate accepted semantic records.
- one source can legitimately yield many semantic/candidate outputs.
- Candidate Case work can evolve without coupling ingestion directly to immutable consumer publication.
- later provider/AI adapters can be introduced behind already tested ports.

## Rejected alternatives

### Let SourceAdapter write canonical Claims/Cases directly

Rejected. It couples providers to domain truth and bypasses review/provenance.

### Let AI task output write ClaimAssessment or CaseDraft directly

Rejected. AI proposal ≠ editorial acceptance and AI is not a truth/publication authority.

### Use one mutable processing row whose JSON is overwritten stage by stage

Rejected. It destroys replay/debug/audit history and makes corrections non-reproducible.

### Keep human review as `RUNNING`/`WAITING` ingestion state

Rejected. Human review is semantic governance over immutable proposals, not machine execution state.

### Auto-create an AuthoringCaseVersion when Candidate Case is accepted

Rejected in this ADR. The projection/mapping into existing authoring fields, review modes, flow selection and source/context presentation needs its own explicit contract.

### Introduce a graph DB or workflow engine now

Rejected. PostgreSQL + ports/adapters + bounded worker/queue are sufficient until measured requirements justify another ADR.
