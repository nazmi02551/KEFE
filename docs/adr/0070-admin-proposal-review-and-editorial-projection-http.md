# ADR-0070 — Secured Admin Proposal Review and Editorial Projection HTTP

**Status:** Accepted for Slice 34 implementation  
**Date:** 2026-08-02  
**Issue:** #192  
**Parent runtime:** PR #190 / Slice 33  
**Capabilities:** CAP-061, CAP-062, CAP-063, CAP-065

## Context

Slice 33 established the active-line provider-neutral ingestion runtime, immutable Proposals, one terminal human review decision and the explicit bridge from accepted reviewed Candidate Case Proposals to the existing Content Authoring DRAFT lifecycle.

The remaining operational gap is a secured Admin command surface. Direct service calls are not an acceptable production boundary, and Proposal acceptance must not silently trigger Editorial Projection or any later authoring lifecycle transition.

## Decision

KEFE will expose two distinct write commands under the existing `/internal/admin/v1` boundary:

1. `POST /proposals/{proposal_id}/review`
   - requires the existing Admin session cookie and same-session CSRF token;
   - requires `CONTENT_REVIEW`;
   - derives `reviewer_ref` from `AdminPrincipal.audit_actor_ref`;
   - records exactly one terminal `ProposalReviewDecision`;
   - does not invoke Editorial Projection.

2. `POST /candidate-proposals/{candidate_proposal_id}/projection`
   - requires the existing Admin session cookie and same-session CSRF token;
   - requires the dedicated `CONTENT_PROJECT` capability;
   - derives projection audit identity from `AdminPrincipal.audit_actor_ref`;
   - accepts an explicit accepted review decision, projection profile and idempotency key;
   - creates or replays one Content Authoring `DRAFT` only.

Both commands use strict request models. Actor identity, roles, capabilities, target lifecycle state and publication intent are forbidden request concerns.

## Authorization

- `REVIEWER` receives `CONTENT_REVIEW` through the existing policy.
- `EDITOR` receives `CONTENT_PROJECT`.
- Proposal review and Editorial Projection remain separate duties and separate HTTP calls.
- This ADR does not redefine the existing Content Authoring submit/review/approve/publish separation-of-duties rules.

## Invariants

- Proposal acceptance is not Editorial Projection.
- Editorial Projection is not Content Authoring submission, approval or publication.
- No automatic transition occurs after Proposal review.
- The resulting CaseVersion remains mutable authoring `DRAFT`; no consumer materialization is created.
- Provider/AI output remains Proposal, never truth authority or autonomous editorial acceptance.
- The existing generic Content Authoring aggregate is reused; no second CMS is introduced.
- Preview fixtures and provider identities do not participate in this Admin boundary.

## Error behavior

- missing/invalid Admin session or CSRF fails before mutation;
- insufficient capability fails closed;
- unknown Proposal returns `INGESTION_PROPOSAL_NOT_FOUND`;
- a second terminal review returns `INGESTION_PROPOSAL_ALREADY_REVIEWED`;
- Editorial Projection retains the ADR-0029 error contract and idempotency behavior.

## Evidence required

Slice 34 is not PASS until the same exact runtime SHA succeeds in:

- API lint, unit, architecture/contract and OpenAPI drift gates;
- PostgreSQL Admin session + review + explicit projection integration;
- MVP Beta Gates;
- Global Readiness.

CI does not establish human editorial usability, external provider operation, deployed production SLO, operator rollback, store compliance or publication quality acceptance.

## Explicit exclusions

No Admin queue UI, Case Builder UI, Flow Composer, bulk review, bulk projection, external provider/AI call, worker/scheduler, autonomous acceptance, authoring submission, approval, publication, consumer Claim Graph remapping or phone-facing behavior is included.
