# Durable Admin Proposal Review Queue and Query Semantics — Slice 36 Candidate

**Issue:** #196  
**Parent:** PR #195 / Slice 35  
**Capabilities:** CAP-061, CAP-065  
**Foundation waves:** F1 → F3 operational bridge  
**Status:** candidate; exact-head CI pending

## Candidate boundary

This slice exposes the existing durable Proposal store to authorized human reviewers without creating a duplicate queue database or second CMS:

`Proposal + IngestionRun + optional terminal ProposalReviewDecision → secured Admin review queue`

Implemented candidate behavior:

- authenticated `GET /internal/admin/v1/proposals` queue endpoint;
- authenticated `GET /internal/admin/v1/proposals/{proposal_id}` detail endpoint;
- `CONTENT_REVIEW` authorization through the existing Admin session boundary;
- deterministic oldest-first `(created_at, proposal_id)` ordering;
- opaque, URL-safe and strictly validated keyset cursor;
- no offset pagination;
- page size 1–100, default 50, with one-extra-row continuation detection;
- exact filters for review state, Proposal kind, risk code, run ID and pipeline code;
- lightweight list records without arbitrary Proposal payload;
- detail records with immutable Proposal payload;
- current terminal review summary assembled from the durable review decision;
- memory and PostgreSQL read-model implementations over existing aggregates;
- immediate queue refresh after the existing explicit review command.

## Preserved boundaries

Queue reads do not:

- claim, reserve, assign or lock a Proposal;
- rank work through AI or autonomous prioritization;
- mutate Proposal or review state;
- trigger Editorial Projection;
- submit, approve or publish Content Authoring state;
- invoke an external source/provider;
- introduce an Admin web UI, Case Builder, Flow Composer or phone behavior.

An accepted Proposal remains only a human review result. Editorial Projection remains a separate explicit command, and projection still creates Content Authoring `DRAFT` only.

## Contract authority

- ADR-0072;
- `docs/contracts/admin-proposal-review-queue-slice36.v1.json`;
- `docs/contracts/admin-http-surface.v1.yaml` v1.3.0;
- `docs/contracts/openapi-admin-proposal-queue.v0.19.overlay.json`.

## Evidence rule

Do not call Slice 36 PASS until the same exact runtime SHA succeeds in:

- API CI lint/unit/architecture/contract/OpenAPI jobs;
- PostgreSQL migration, seed, queue pagination/filter/detail/review-refresh integration;
- MVP Beta Gates;
- Global Readiness.

Automated evidence does not establish human reviewer usability, queue assignment/lease concurrency, external provider operation, deployed SLO or operator rollback readiness.
