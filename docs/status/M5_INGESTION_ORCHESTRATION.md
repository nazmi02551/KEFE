# M5 Ingestion Orchestration Checkpoint

**Date:** 2026-07-29  
**Repository:** `nazmi02551/KEFE`  
**Architecture lock:** PR #67 / ADR-0028  
**Architecture merge:** `033e182eb7241006b32f880ec81fed6ec8fe6e7b`  
**Runtime implementation:** PR #68  
**Runtime merge:** `19776494dd020f1e606da2eeae02280170387714`

This checkpoint supplements `docs/status/CURRENT.md` and exists to make the post-M4 continuation durable even before the next publication milestone.

## Architecture lock — PR #67

Exact head: `b665e7f9131586e157aedc8c2203d54b83387f54`  
API CI: `30442576111` PASS, including PostgreSQL integration.

ADR-0028 locks a separate provider-neutral ingestion-orchestration bounded context:

- orchestration is neither Claim truth authority nor Case publication authority;
- provider-specific SDKs, credentials and payload types stop at `SourceAdapter`;
- canonical inputs are `SourceArtifact` / `NormalizedArtifact` references;
- pipeline/stage identity is versioned and extensible;
- `IngestionRun` is replay-safe and content/config/version pinned;
- `StageExecution` attempts are append-only and bounded;
- semantic stage output is immutable `Proposal`, never direct canonical mutation;
- human/editorial review is a separate durable decision;
- AI/provider output cannot self-accept or publish;
- accepted knowledge proposals materialize through an idempotent boundary;
- accepted DecisionProblem/QuestionDraft/CandidateCase remains upstream of Content Authoring until a later projection contract;
- external content is untrusted input; retries/concurrency/external calls must be bounded;
- consumer Weigh/Commit/Reveal must not depend on ingestion/provider availability.

Architecture contract: `docs/contracts/ingestion-orchestration.v1.yaml` v1.0.0 at the lock merge.  
Manifest at the lock merge: v1.34.0.

## Runtime implementation — PR #68

Exact green head: `0535b48a1fcd6709a3e557b02acf290d8c094a04`  
API CI: `30446286467` PASS.

Implemented:

- durable `IngestionRun` with deterministic run key over artifact/hash/pipeline/config/version/scope;
- run states: QUEUED, RUNNING, SUCCEEDED, FAILED_RETRYABLE, FAILED_FINAL, CANCELED;
- append-only `StageExecution` with bounded attempt/max-attempt invariants;
- provider-neutral `StageProcessor`, orchestration repository and proposal materializer ports;
- immutable `Proposal` with stable payload hashing and supersession lineage;
- one terminal human `ProposalReviewDecision` per proposal; reconsideration requires a superseding proposal;
- accepted-only `ProposalMaterialization` ledger;
- deterministic canonical target identity for knowledge materialization;
- crash/retry-safe materialization: existing deterministic target is verified rather than treating arbitrary persistence errors as replay success;
- accepted materialization for CLAIM, CLAIM_ASSESSMENT, CLAIM_ASSERTION, EVIDENCE_LINK, CLAIM_RELATION, ARGUMENT and ARGUMENT_RELATION;
- human reviewer identity is preserved for accepted ClaimAssessment materialization;
- ADR-0027 invariants remain binding: EvidenceLink does not mutate ClaimAssessment; ClaimAssertion does not mutate Claim State;
- in-memory and PostgreSQL persistence adapters;
- migration `20260729_0016_ingestion_orchestration.py` creating the isolated `ingestion` schema;
- persistence builder wiring;
- dedicated architecture fitness gate;
- unit and PostgreSQL integration coverage.

Implementation contract: `ingestion-orchestration.v1.yaml` v1.1.0.  
Manifest: v1.35.0.  
OpenAPI remains 0.16.0 because no HTTP surface was added.

Exact-head CI `30446286467` verified:

- lint PASS;
- contract sync PASS;
- Case Flow pinning PASS;
- generic Flow runtime PASS;
- DecisionRevision lineage PASS;
- Reflection runtime PASS;
- Claim/Argument ingestion PASS;
- Ingestion orchestration PASS;
- Admin HTTP contract PASS;
- unit tests PASS;
- OpenAPI drift PASS;
- PostgreSQL migration/seed/integration PASS.

## Explicitly not implemented

- external source-provider/crawler SDK calls;
- AI provider calls;
- CandidateCase / DecisionProblem / QuestionDraft → Content Authoring DRAFT projection;
- automatic publication;
- consumer Claim Graph or ingestion UI;
- Admin queue UI;
- Context Claim-status remapping;
- graph database.

## Next locked-development rule

The next behavior must be locked before code.

The natural next boundary is **editorial projection**: define exactly how reviewed/accepted `CANDIDATE_CASE`, `DECISION_PROBLEM` and `QUESTION_DRAFT` proposals become a new DRAFT in the existing Content Authoring bounded context while preserving provenance, idempotency, risk/review policy, Flow selection and the existing DRAFT → IN_REVIEW → APPROVED → PUBLISHED authority.

Do not implement that mapping, external provider calls, AI calls or automatic publication until the corresponding ADR + machine-readable contract is accepted.
