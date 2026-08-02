# Ingestion Worker Runner — Slice 38 Candidate

**Date:** 2026-08-02  
**Issue:** #200  
**Parent runtime:** PR #199 / Slice 37  
**Branch:** `feature/ingestion-worker-runner-slice38`  
**Status:** Candidate — exact-head evidence pending

## Candidate scope

This slice connects the durable provider-neutral ingestion orchestration and Slice 37 worker lease boundary through a synchronous one-shot runner.

Candidate behavior:

- exact `(pipeline_code, pipeline_version)` runtime plans;
- exact versioned stage processor registry;
- code+version filtered lease claim;
- at most one claimed run per invocation;
- deterministic successful-stage resume and chained stage input hashes;
- heartbeat before processor invocation;
- lease heartbeat/admission callback immediately before every stage outcome or Proposal persistence;
- no stage, Proposal or run-state mutation after lease loss at that boundary;
- successful completion marks the run `SUCCEEDED` and releases terminal ownership;
- retryable/final stage outcomes retain existing orchestration semantics and do not schedule their own retry;
- privacy-safe bounded operational result and observer port;
- empty default production registry and no-op observer.

## Preserved boundaries

The candidate does not add:

- a daemon or continuous loop;
- scheduler cadence, cron or process supervision;
- a provider adapter, network request or AI call;
- automatic run creation, retry or requeue policy;
- Proposal review or Editorial Projection automation;
- Content Authoring lifecycle transitions;
- Admin HTTP/UI, Case Builder or Flow Composer;
- phone-facing behavior.

## Evidence still required

Do not call this slice PASS until one exact runtime SHA proves:

- lint and all existing architecture contracts;
- the Slice 38 architecture gate;
- memory exact-plan, hash-chain, resume, lease-loss and failure behavior;
- PostgreSQL exact-version claim and crash/reclaim resume behavior;
- OpenAPI drift remains unchanged;
- API CI, MVP Beta Gates and Global Readiness all succeed on the same head SHA.

This candidate does not establish external provider operation, a running scheduler, OS process supervision, deployed SLO, operator usability or rollback readiness.
