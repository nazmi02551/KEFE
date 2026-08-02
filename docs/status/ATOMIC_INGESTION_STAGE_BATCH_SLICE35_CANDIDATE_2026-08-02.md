# Atomic Ingestion Stage Completion and Proposal Batch — Slice 35 Candidate

**Issue:** #194  
**Parent:** PR #193 / Slice 34  
**Capabilities:** CAP-055, CAP-061  
**Foundation wave:** F1 completion hardening  
**Status:** candidate; exact-head CI pending

## Candidate boundary

This slice closes the partial-success gap in the provider-neutral ingestion runtime:

`StageProcessorResult → SUCCEEDED StageExecution + complete immutable Proposal batch`

The successful StageExecution and all Proposals emitted by that result now form one repository transaction boundary.

Implemented candidate behavior:

- complete Proposal tuple constructed before persistence;
- one `complete_successful_stage(...)` repository call from the service success path;
- one memory critical section and one PostgreSQL transaction;
- run must exist and remain `RUNNING` during completion;
- Proposal run/stage ownership and duplicate IDs validated;
- external supersession targets must exist in the same run;
- same-batch supersession is supported through deterministic dependency-safe ordering;
- supersession cycles fail closed;
- one invalid Proposal leaves no successful stage or partial Proposal batch;
- no schema migration.

## Preserved boundaries

This slice does not add:

- worker, scheduler, lease or queue-claim behavior;
- external source or AI provider calls;
- Admin queue/query/UI;
- autonomous Proposal review;
- automatic Editorial Projection;
- Content Authoring submit, approval or publication;
- Case Builder or Flow Composer;
- phone-facing behavior.

Processor failure-attempt recording remains separate and unchanged. An atomic success persistence failure leaves the run `RUNNING`; later worker/operator retry or termination policy is outside this slice.

## Contract authority

- ADR-0071;
- `docs/contracts/atomic-ingestion-stage-batch-slice35.v1.json`;
- existing ADR-0028 and ingestion orchestration contract remain authoritative for provider neutrality and review separation.

## Evidence rule

Do not call Slice 35 PASS until the same exact runtime SHA succeeds in:

- API CI lint/unit/contract/OpenAPI jobs;
- PostgreSQL migration, seed and atomic rollback/visibility integration;
- MVP Beta Gates;
- Global Readiness.

Automated evidence does not establish production worker crash recovery, external provider operation, deployed SLO, human editorial usability or operator rollback readiness.
