# ADR-0092 — Approved public-feed manual capture execution

- Status: Accepted
- Date: 2026-08-03
- Slice: 56

## Context

Slice 55 introduced a durable, secured and empty-by-default public-feed catalog. A catalog entry can become `MANUAL_CAPTURE_APPROVED`, but no operation yet consumes that approval. The next boundary must execute one capture without bypassing provider admission, controlled HTTP, immutable evidence or Commit First, and without silently introducing a scheduler or automatic editorial workflow.

A global mutable provider/adoption registry would make per-feed activation difficult to reason about and could leave partially configured runtime state after failures. The exact immutable catalog definition should instead be the sole source for an invocation-scoped runtime.

## Decision

KEFE introduces `ApprovedPublicFeedManualCaptureService`.

An invocation requires:

- an authenticated Admin with `SOURCE_MANAGE`;
- same-session CSRF at the HTTP boundary;
- fresh step-up authentication;
- an existing catalog entry in exactly `MANUAL_CAPTURE_APPROVED`;
- the immutable catalog definition and configuration hash.

Request payloads cannot supply adapter code, locator, HTTP/parser budgets, capability settings, pipeline identity or configuration hash.

For each invocation, a runtime factory creates an ephemeral exact runtime from the immutable definition:

1. one exact provider adoption profile and adoption registry;
2. one controlled provider HTTP transport using the configured shared DNS resolver and pinned backend;
3. one strict RSS/Atom evidence-backed capture adapter and public capture registry;
4. one permit-bound public capture executor;
5. one SourceAcquisitionService using the shared admission/context, evidence, knowledge and ingestion repositories.

The exact PUBLIC provider capability derived from the definition is registered idempotently before acquisition. Conflicting capability configuration fails closed. Global startup capture/adoption registries remain empty and are never mutated.

Exactly one `SourceAcquisitionCommand` and one acquisition attempt are emitted per service invocation. `SourceAcquisitionService` may commit an immutable SourceArtifact and queue one ingestion run, preserving Commit First and Blind First. The manual service never runs an ingestion worker, creates a schedule, reviews or materializes proposals, creates a Case, or publishes content.

Every attempt is appended to a dedicated execution audit repository. Audit contains the catalog entry ID, feed code, configuration hash, server-derived Admin actor, trace ID, bounded outcome/error code, SourceArtifact ID, ingestion run ID, duration and timestamp. It never stores the locator, response body, storage backend object key, credentials, secret references, HTTP headers or exception text.

Memory and PostgreSQL audit repositories provide equivalent behavior. PostgreSQL audit rows are append-only.

Production startup composes the service and runtime factory but seeds zero catalog entries. Provider HTTP runtime mode and raw-evidence mode remain fail-closed when unconfigured.

## Consequences

- Approved catalog definitions become executable without persistent mutable adapter registries.
- Every attempt is operationally auditable.
- Capture can commit evidence and queue ingestion, but no downstream editorial action is automatic.
- A later scheduler can reuse the same approved execution primitive under a separate ADR.

## Non-goals

This ADR does not select or seed a publisher, prove production egress or durable object storage, run ingestion workers automatically, create recurring schedules, automate review/materialization/publication, or add an Admin web UI or phone-facing feed controls.