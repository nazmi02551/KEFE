# Source Acquisition Admission — Slice 39 Candidate

**Date:** 2026-08-02  
**Issue:** #202  
**Parent runtime:** PR #201 / Slice 38  
**Branch:** `feature/source-acquisition-admission-slice39`  
**Status:** Candidate — exact-head evidence pending

## Candidate scope

This slice adds a provider-neutral one-shot boundary from an exact versioned source capture adapter to the existing immutable `SourceArtifact` and idempotent `IngestionRun` aggregates.

Candidate behavior:

- immutable versioned adapter codes ending in `.vN`;
- exact adapter resolution and duplicate registration rejection;
- bounded `CapturedSource` metadata with content hash and optional opaque storage reference;
- no raw source body, provider response, SDK type or credential across the port;
- existing SourceArtifact fingerprint replay;
- existing deterministic IngestionRun key replay;
- unchanged content returns the same artifact and run identities;
- changed content hash creates a new immutable artifact and run;
- preexisting artifact without a run is completed by replay;
- typed retryable/final capture failures and privacy-safe unexpected failure mapping;
- privacy-safe result/observer allowlist;
- observer failure does not change acquisition result;
- empty default application registry and no-op observer.

## Preserved boundaries

The candidate does not add:

- a real X, YouTube, RSS, news or browser adapter;
- a network request, scraping or browser automation;
- provider credentials or SDK dependencies;
- AI calls or normalization;
- scheduler/daemon, automatic retry/requeue or worker invocation;
- Proposal review/projection or authoring lifecycle transitions;
- Admin HTTP/UI, Case Builder or Flow Composer;
- phone-facing behavior.

## Evidence still required

Do not call this slice PASS until one exact runtime SHA proves:

- lint and all prior architecture gates;
- the Slice 39 source acquisition architecture gate;
- memory replay, changed-content, preexisting-artifact recovery and zero-write failures;
- PostgreSQL replay, changed-content and recovery parity;
- unchanged OpenAPI output;
- API CI, MVP Beta Gates and Global Readiness all succeed on the same head SHA.

This candidate does not establish external provider operation, terms compliance, rate-limit handling, a deployed scheduler, production SLO, operator usability or rollback readiness.
