# Source Acquisition Scheduler — Slice 40 Candidate

**Date:** 2026-08-02  
**Issue:** #204  
**Parent runtime:** PR #203 / Slice 39  
**Branch:** `feature/source-acquisition-scheduler-slice40`  
**Status:** Candidate — exact-head evidence pending

## Candidate scope

This slice adds a durable provider-neutral fixed-interval schedule and dispatch ledger around the existing Slice 39 source acquisition service.

Candidate behavior:

- immutable exact acquisition schedule configuration;
- UTC fixed intervals from 60 seconds to 30 days;
- explicit ACTIVE, PAUSED and RETIRED lifecycle;
- one-shot oldest-first `plan_due_once` with no execution-time drift;
- unique `(schedule_id, due_at)` occurrence ledger;
- one-shot oldest-first `execute_pending_once` with exclusive expiring ownership;
- PostgreSQL `FOR UPDATE SKIP LOCKED` for planner and executor replicas;
- bounded dispatch attempts and stale recovery;
- PENDING recovery while attempts remain and FINAL_FAILURE on exhaustion;
- heartbeat before capture, SourceArtifact persistence, IngestionRun admission and dispatch completion;
- replay-safe recovery after an artifact or complete acquisition was persisted before dispatch completion;
- terminal mapping for admitted, retryable, final and blocked acquisition outcomes;
- privacy-safe dispatch result/observer allowlist;
- empty default schedule ledger, empty provider registry and no background loop.

## Preserved boundaries

The candidate does not add:

- cron expressions or local-time/DST cadence;
- a continuous daemon, OS process manager or deployment manifest;
- a real provider adapter, network request, scraping or browser automation;
- provider credentials, AI calls or normalization;
- automatic schedule creation or failure retry/backoff;
- ingestion worker invocation;
- Proposal review/projection or authoring lifecycle transitions;
- Admin HTTP/UI, Case Builder or Flow Composer;
- phone-facing behavior.

## Evidence still required

Do not call this slice PASS until one exact runtime SHA proves:

- migration upgrade, downgrade and return to one head;
- all prior and Slice 40 architecture gates;
- memory lifecycle, no-drift planning, ownership, stale recovery, attempt exhaustion, persistence guards, replay and observer isolation;
- PostgreSQL planner/executor concurrency, stale recovery and crash replay;
- unchanged OpenAPI output;
- API CI, MVP Beta Gates and Global Readiness all succeed on the same head SHA.

This candidate does not establish a running daemon, external provider operation, provider terms compliance, deployed SLO, operator usability or rollback readiness.
