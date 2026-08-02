# Secured Admin Proposal Review and Editorial Projection HTTP — Slice 34 Candidate

**Issue:** #192  
**Parent:** PR #190 / Slice 33  
**Capabilities:** CAP-061, CAP-062, CAP-063, CAP-065  
**Foundation waves:** F2 → F3  
**Status:** candidate; exact-head CI pending

## Candidate boundary

This slice exposes the active-line reviewed Proposal and Editorial Projection runtimes through the existing secured Admin HTTP boundary:

`Admin session + same-session CSRF → explicit Proposal review → separate explicit Editorial Projection → Content Authoring DRAFT`

Implemented candidate behavior:

- terminal `ProposalReviewDecision` command at `/internal/admin/v1/proposals/{proposal_id}/review`;
- server-derived `reviewer_ref` and `CONTENT_REVIEW` authorization;
- explicit Editorial Projection command at `/internal/admin/v1/candidate-proposals/{candidate_proposal_id}/projection`;
- server-derived projection identity and dedicated `CONTENT_PROJECT` authorization;
- strict request models that reject request-supplied actor/admin/lifecycle fields;
- deterministic response records;
- idempotent projection replay;
- memory and PostgreSQL HTTP evidence;
- additive Admin OpenAPI overlay and 0.19/0.20 composition updates;
- architecture fitness enforcing that Proposal review cannot call projection.

## Preserved lifecycle separation

An `ACCEPTED` Proposal review does not create an authoring CaseVersion and does not invoke Editorial Projection.

Editorial Projection is a second explicit command. It creates or replays one existing Content Authoring `DRAFT` and does not:

- submit the DRAFT for authoring review;
- approve or publish it;
- create a consumer `CaseVersion`;
- materialize it into the consumer Claim Graph or Context state;
- invoke an external source or AI provider.

## Contract authority

- ADR-0070;
- `docs/contracts/admin-editorial-operations-slice34.v1.json`;
- `docs/contracts/admin-http-surface.v1.yaml` v1.2.0;
- `docs/contracts/openapi-admin-projection.v0.19.overlay.json`.

## Evidence rule

Do not call Slice 34 PASS until the same exact runtime SHA succeeds in:

- API CI lint/unit/contract/OpenAPI jobs;
- PostgreSQL migration and Admin review/projection HTTP integration;
- MVP Beta Gates;
- Global Readiness.

A later documentation-only commit must not replace the verified runtime SHA in status reporting.

## Explicit exclusions

No Admin queue UI, Case Builder UI, Flow Composer, provider/AI delivery, worker/scheduler, bulk review/projection, autonomous acceptance, authoring approval/publication, phone-facing behavior, human editorial usability acceptance, deployed SLO or operator rollback evidence is included.
