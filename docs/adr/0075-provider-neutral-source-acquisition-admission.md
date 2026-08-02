# ADR-0075 — Provider-Neutral Source Acquisition and Idempotent Ingestion Admission

**Status:** Accepted for Slice 39 implementation  
**Date:** 2026-08-02  
**Issue:** #202  
**Parent runtime:** PR #201 / Slice 38  
**Capabilities:** CAP-054, CAP-055, CAP-065  
**Foundation wave:** F1 source acquisition boundary

## Context

KEFE now has immutable Knowledge artifacts, provider-neutral IngestionRuns, atomic stage/Proposal persistence, exclusive worker leases and a one-shot lease-supervised runner. No production-safe boundary currently converts an external locator into a canonical `SourceArtifact` and admits it into an exact pipeline without leaking provider SDK objects or raw source bodies into the domain.

The existing broad `SourceAdapter` protocol predates the runtime adoption path and combines capture with normalization. Slice 39 must not invoke provider-specific normalization or create a second artifact model. It must adopt the existing canonical `SourceArtifact` and `IngestionRun` aggregates through a smaller capture-only port.

## Decision

KEFE will add a synchronous one-shot `SourceAcquisitionService.acquire(...)` boundary.

### Exact adapter identity

- `adapter_code` is an immutable, explicitly versioned capability identifier using the form `<namespace>.<name>.v<positive integer>`.
- A behaviorally incompatible adapter implementation requires a new adapter code. An existing code may not silently change capture semantics.
- Adapter resolution is exact only. Locator shape, domain name, title, locale, payload content or Case type may not select an adapter.
- Duplicate adapter codes fail at registry construction.
- The production application composition uses an empty registry until a separately reviewed provider adoption slice registers an adapter.

### Provider-neutral capture envelope

The adapter returns only `CapturedSource` metadata:

- content hash;
- optional external ID and canonical URL;
- optional publisher/issuer and published timestamp;
- optional language and jurisdiction;
- optional opaque raw-storage reference.

Raw source text/body/bytes, provider response objects, SDK types, credentials, access tokens and cookies may not cross the port. The raw body, when a future provider requires it, must first be written to an approved storage boundary and represented only by the opaque storage reference.

### Canonical artifact and run admission

- The service constructs the existing immutable `SourceArtifact` using the exact adapter code, requested external locator and captured content hash.
- Persistence uses the existing unique fingerprint `(adapter_code, external_locator, content_hash)`.
- The persisted or replayed artifact is admitted through the existing `IngestionOrchestrationService.start_run(...)` using exact pipeline code/version/configuration and optional taxonomy/methodology/locale/jurisdiction pins.
- The existing deterministic run key provides idempotent run admission.
- Repeating an unchanged capture returns the same SourceArtifact and IngestionRun identities.
- A changed content hash creates a new immutable SourceArtifact and a new IngestionRun.

Artifact persistence and run admission are a recoverable two-write sequence rather than a fabricated cross-module transaction. If the artifact becomes durable and run admission fails, the artifact remains canonical. Replaying the same command reuses that artifact and completes run admission without duplication. The service never deletes the artifact as compensation.

### Failure classes

- `RetryableSourceCaptureError` produces `RETRYABLE_FAILURE` with a bounded error code and no writes.
- `FinalSourceCaptureError`, invalid capture envelope or adapter contract violation produces `FINAL_FAILURE` with no writes.
- Unexpected adapter exceptions are mapped to `FINAL_FAILURE` without exception text.
- Persistence/admission infrastructure exceptions are mapped to `RETRYABLE_FAILURE`; a replay is safe.
- Missing exact adapter registration produces `BLOCKED` without writes.

### Operational result

Every invocation returns and emits one privacy-safe `SourceAcquisitionResult` with an outcome from:

- `ADMITTED`
- `RETRYABLE_FAILURE`
- `FINAL_FAILURE`
- `BLOCKED`

Allowed fields are exact adapter/pipeline identity, trace ID, duration, optional SourceArtifact/IngestionRun IDs and bounded error code. Source text/body, provider response, Proposal payload, private reason, credentials, exception text, consumer identity, ideology/personality/psychometric data and causal inference are forbidden.

Observer failure may not change the acquisition result or persistence outcome.

## Explicit exclusions

No real X, YouTube, RSS, news or browser adapter; network request; scraping; browser automation; AI call; normalization; scheduler/daemon; automatic retry/requeue; worker invocation; Proposal review/projection; authoring transition; Admin HTTP/UI; Case Builder; Flow Composer; or phone behavior is included.

## Evidence required

Slice 39 is not PASS until one exact runtime SHA proves:

- exact versioned adapter validation and duplicate rejection;
- empty production registry;
- unchanged replay returns identical artifact and run IDs;
- changed hash creates new immutable identities;
- preexisting artifact without a run is recovered by replay;
- retryable/final/missing-adapter failures produce no artifact or run;
- raw payload/provider response/credential fields cannot cross the capture model or observer result;
- memory and PostgreSQL behavior parity;
- architecture fitness, API CI, MVP Beta Gates and Global Readiness success.

Automated evidence does not establish a functioning external provider, provider terms compliance, rate-limit behavior, deployed scheduler, SLO, operator usability or rollback readiness.
