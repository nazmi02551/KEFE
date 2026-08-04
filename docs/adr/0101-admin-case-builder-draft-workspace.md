# ADR-0101: Bounded Admin Case Builder DRAFT Workspace

- **Status:** Accepted for implementation
- **Date:** 2026-08-04
- **Issue:** #298
- **Parent runtime:** PR #297 / `59f70896c8d9df91727c158da936630bd6bddd6c`
- **Capabilities advanced without lifecycle promotion:** CAP-062, CAP-063, CAP-065, CAP-095, CAP-126

## Context

The canonical content-supply line can now produce an independently reviewed Candidate Case and explicitly project it into the existing Content Authoring aggregate as one `DRAFT`. PR #297 exposes that source-review → candidate-bundle → explicit projection lifecycle through a secured Admin Studio operations client.

The next operator gap is not a new content model. It is the absence of a usable editor for the already-existing `AuthoringCaseVersion`. The repository already owns:

- one Content Authoring aggregate and lifecycle;
- one secured Admin session, capability and same-session CSRF boundary;
- immutable published CaseVersion semantics;
- explicit submit, review, approval and publication commands;
- append-only lifecycle audit;
- pinned Flow/configuration provenance at publication.

Creating a second CMS, duplicating Case/Flow ownership or mixing edit/save/submit/review/publish into one command would violate the canonical architecture.

## Decision

Implement a bounded Admin Studio **Case Builder DRAFT workspace** over the existing Content Authoring aggregate.

### API boundary

1. Add an additive Case Builder adapter with:
   - `GET /internal/admin/v1/case-builder/case-versions/{version_id}`;
   - `PUT /internal/admin/v1/case-builder/case-versions/{version_id}`.
2. The adapter delegates reads and saves to the existing `SecuredContentAuthoringService`; it owns no repository, lifecycle or publication authority.
3. Reuse the existing `POST /internal/admin/v1/case-versions/{version_id}/submit` command.
4. Reuse the existing `GET /internal/admin/v1/cases/{case_id}/audit` operation.
5. Reads require an authenticated Admin principal with `CONTENT_EDIT`; writes continue to require same-session CSRF and the existing capability checks.
6. The Case Builder adapter exposes complete operator-safe canonical fields needed to round-trip a DRAFT, including locale/market/context notes, localizations and read-only Flow template identity.
7. The existing legacy create/save authoring routes remain unchanged. This avoids silently changing their request contract while allowing the richer editor to preserve every canonical field explicitly.
8. Flow template identity is response-only in the Case Builder adapter and therefore cannot be rewritten by the Case Builder.
9. Raw evidence bytes, credentials, secrets, storage references and backend object keys are never part of the Case Builder response.

### Admin Studio boundary

The workspace:

- loads only after an explicit operator command;
- may prefill the exact version ID from a `version` query parameter but never fetches on mount;
- edits core metadata, issues/questions, context blocks, source references, risk/fact flags, review modes and market/locale notes;
- shows Flow template code/version as read-only because CAP-064 Flow Composer remains a separate authority;
- saves only after an explicit operator command;
- submits for review only through a separate explicit command;
- shows lifecycle audit only after an explicit operator command and only when authorized;
- never autosaves, auto-submits, auto-reviews, auto-approves or auto-publishes;
- renders API error text as bounded text, never as markup;
- persists neither session nor CSRF material.

### Lifecycle boundary

This slice may transition only:

- `DRAFT → DRAFT` through save;
- `DRAFT → IN_REVIEW` through explicit submit.

The Case Builder does not expose approve, reject, publish or withdraw controls. Maker-checker review remains a separate future operator surface.

## Consequences

### Positive

- The verified Candidate Case projection becomes human-operable without a second CMS.
- Existing aggregate, authorization, audit and lifecycle rules remain authoritative.
- The legacy authoring HTTP contract is not broadened or silently reinterpreted.
- The rich adapter can round-trip canonical locale/market/localization fields without loss.
- Flow composition remains independently governed.
- The operator can inspect exactly what will enter review before submitting.

### Costs

- The first Case Builder is intentionally a structured form rather than a visual Flow composer.
- The Admin API gains one additive operator-oriented adapter surface.
- Human editorial usability and CQB acceptance still require external review.

## Rejected alternatives

### A second Admin-only Case model

Rejected because it would create parallel content truth, migration and publication semantics.

### Broadening the legacy `PUT /case-versions/{id}` request

Rejected because existing clients use a strict full-body contract that does not contain all current canonical fields. Adding defaults could silently overwrite projected locale/market values, while making fields newly required would break existing clients.

### Combined save-and-submit

Rejected because operators must be able to save incomplete work without accidentally moving lifecycle state.

### Editing Flow topology inside the Case Builder

Rejected because CAP-064 requires a separately versioned Flow Composer and publication resolver authority.

### Browser-side autosave

Rejected because it creates hidden mutations, ambiguous audit expectations and accidental lifecycle coupling.

## Verification requirements

The implementation is not PASS until one exact child SHA has:

- executable Case Builder architecture contract;
- API lint, OpenAPI drift, memory behavior and PostgreSQL restart/round-trip evidence;
- Admin client security and deterministic draft round-trip tests;
- semantic component/accessibility tests and production Next.js build;
- dedicated Case Builder CI;
- API CI, Admin Studio CI, Mobile CI, MVP Beta Gates and Global Readiness.

CI does not prove human usability/CQB acceptance, real provider delivery, production deployment, SLO/load/observability, operator rollback, store compliance or production release.