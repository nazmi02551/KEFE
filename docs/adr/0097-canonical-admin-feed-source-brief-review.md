# ADR-0097 — Canonical Admin Feed Item and Source Brief Review

- Status: Accepted for execution
- Date: 2026-08-04
- Issue: #289
- Parent convergence: ADR-0096 / PR #288
- Capabilities: CAP-061, CAP-065, CAP-095, CAP-126

## Context

PRs #260, #262 and #264 contain exact-head verified typed Admin behavior for Feed Item review, explicit accepted Feed Item normalization into a separate deterministic Source Brief ingestion run, and lineage-safe Source Brief review. Those branches diverge from the current consumer/mobile line after PR #232. They cannot become active merely by having green isolated CI.

The canonical integration line is the PR #288 line stacked on the current progressive phone runtime. This ADR adopts the bounded Admin review behavior onto that line without importing the unresolved public-feed catalog/subscription alternatives.

## Decision

The canonical runtime will expose three strictly separated Admin operations:

1. typed read-only Feed Item list/detail;
2. explicit accepted Feed Item normalization and Source Brief build command;
3. typed read-only Source Brief list/detail.

The existing generic Proposal review mutation remains the only review mutation. Review, normalization/materialization, Source Brief construction, Candidate Case creation, editorial projection, authoring approval and publication remain separate operations.

### Feed Item read boundary

The typed adapter must:

- select only the exact FEED_ITEM proposal kind, risk code and pipeline;
- validate Proposal schema/version/configuration against the immutable IngestionRun;
- validate bounded typed payload values;
- verify SourceArtifact identity, content hash and canonical evidence reference;
- hide arbitrary Proposal payloads from list responses;
- expose no raw evidence body, credential, secret or backend object key.

### Source Brief build boundary

The build command must:

- require an existing terminal ACCEPTED Feed Item review;
- normalize the exact accepted Feed Item into one deterministic immutable NormalizedArtifact;
- start a separate deterministic SOURCE_BRIEF ingestion run;
- emit exactly one review-required SOURCE_BRIEF Proposal;
- be idempotent and recover exact successful stage/proposal history;
- fail closed on schema, lineage, hash, review or atomic-batch drift;
- never review, accept, project or publish the Source Brief automatically.

### Source Brief read boundary

The typed adapter must:

- select only exact SOURCE_BRIEF proposals from the exact pipeline;
- validate Proposal/run/configuration/schema/risk identity;
- re-read the exact NormalizedArtifact and validate canonical metadata hash/schema;
- re-read the exact parent Feed Item through the typed Feed Item adapter;
- require the parent review to remain terminal ACCEPTED;
- verify complete SourceArtifact, content-hash, evidence-reference, normalized-artifact and parent-review lineage;
- omit synopsis and evidence reference from list records;
- expose only bounded typed metadata in detail records;
- expose no raw evidence bytes or backend storage keys.

## API versioning

- API 0.21 adds typed Feed Item reads.
- API 0.22 adds the explicit Source Brief build command.
- API 0.23 adds typed Source Brief reads.
- Earlier API versions must remain unchanged.

## Security

Existing Admin session, CSRF, step-up and capability-first authorization remain authoritative. Read surfaces reuse the existing review capability. The build command remains CSRF-protected and explicitly invoked.

## Exclusions

This slice does not include:

- PR #267 or PR #273 public-feed model selection;
- real provider/feed activation or live scheduling;
- Admin web UI;
- raw evidence viewer or dereference endpoint;
- AI enrichment, semantic or causal inference;
- Candidate Case generation;
- Editorial Projection;
- Case Builder or Flow Composer;
- automatic review, approval or publication;
- mobile/consumer UI changes;
- Signal, Impact, production deployment or store release.

## Evidence

Completion requires the exact integrated SHA to pass:

- dedicated canonical Admin review convergence checks;
- API CI;
- Mobile CI;
- MVP Beta Gates;
- Global Readiness;
- memory and PostgreSQL lineage/idempotency tests;
- API version isolation and OpenAPI exactness.

CI does not establish human usability, editorial CQB acceptance, production provider compliance, deployed SLO or store readiness.

## Rollback

The new routers remain API-version gated. Rollback disables the later API version or removes the router registrations without altering existing Proposal, review, SourceArtifact, NormalizedArtifact or consumer records. No destructive migration is introduced by this slice.