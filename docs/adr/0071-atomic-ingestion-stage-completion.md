# ADR-0071 — Atomic Ingestion Stage Completion and Proposal Batch

**Status:** Accepted for Slice 35 implementation  
**Date:** 2026-08-02  
**Issue:** #194  
**Parent runtime:** PR #193 / Slice 34  
**Capabilities:** CAP-055, CAP-061  
**Foundation wave:** F1 completion hardening

## Context

The active ingestion runtime currently persists a successful `StageExecution` and then persists each emitted immutable `Proposal` in separate repository calls. PostgreSQL therefore commits the stage row before the Proposal batch. A later constraint, process or connection failure can leave a stage visible as `SUCCEEDED` while only part—or none—of its declared output Proposal batch exists.

That state is incompatible with replay-safe provider-neutral orchestration. Downstream human review, Editorial Projection and future Admin queue reads must never infer a complete stage output from a partially persisted batch.

## Decision

A successful stage result is one repository transaction boundary:

`SUCCEEDED StageExecution + complete immutable Proposal batch`

The orchestration service will construct the complete Proposal tuple before any success persistence call and invoke one repository operation. Both memory and PostgreSQL repositories must validate the full batch before making it visible.

The atomic operation must enforce:

- the stage outcome is `SUCCEEDED` and terminal completion metadata is present;
- the owning `IngestionRun` exists and is `RUNNING`;
- every Proposal belongs to the same run and references that exact StageExecution;
- Proposal IDs are unique within the batch and do not already exist;
- supersession references exist, remain within the same run and contain no cycle;
- all batch rows commit together or no stage/Proposal row becomes visible.

A Proposal may supersede another Proposal in the same batch. Repositories must use a deterministic dependency-safe insertion order rather than requiring provider output order to match database foreign-key order.

## Failure semantics

- validation failure occurs before memory mutation;
- PostgreSQL validation or insert failure rolls back the complete transaction;
- a failed atomic completion does not synthesize a successful stage record;
- the run remains `RUNNING`, allowing an operator/worker policy to retry or terminate it explicitly;
- existing retryable/final processor failure recording remains unchanged in this slice.

## Architecture boundary

- provider and AI types remain outside the ingestion domain and repository port;
- the service may not persist a successful StageExecution and its Proposals one-by-one;
- Proposal review, projection, authoring approval and publication remain separate commands;
- this ADR introduces no worker, scheduler, lease, queue claim, external provider or Admin UI.

## Evidence required

Slice 35 is not PASS until the same exact runtime SHA proves:

- successful stage and complete batch visibility in memory and PostgreSQL;
- full rollback when one batch Proposal is invalid;
- deterministic same-batch supersession ordering and cycle rejection;
- architecture fitness preventing one-by-one success persistence;
- API CI, MVP Beta Gates and Global Readiness success.

Automated evidence does not establish external provider operation, worker crash recovery, deployed SLO, human editorial usability or operator rollback readiness.
