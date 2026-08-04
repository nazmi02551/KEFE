# ADR-0104: Bounded Admin Publication Operations Workspace

- Status: Accepted for implementation
- Date: 2026-08-04
- Issue: #304
- Parent runtime: PR #303 exact verified head `62dd27dfa2000d818cecf16af9627c54f98a245a`
- Primary capability: CAP-065
- Supporting capabilities: CAP-063, CAP-126

## Context

KEFE already has one canonical Content Authoring aggregate and lifecycle service. That service owns `DRAFT → IN_REVIEW → APPROVED → PUBLISHED → WITHDRAWN`, validates publication, pins the published `ContentConfigurationSnapshot` and resolved Flow, persists lifecycle transitions atomically, and appends audit entries.

The generic secured Admin HTTP surface exposes publish and withdraw commands, but the Admin Studio has no bounded publisher workspace, no deterministic APPROVED/PUBLISHED queue, no explicit publication preflight, and no publisher-versus-approver maker-checker enforcement. Leaving publication as an unstructured low-level command would make the operational lifecycle difficult to inspect and easier to misuse.

A new surface must not become a second CMS, second lifecycle authority, alternate publication resolver, or automatic publishing pipeline.

## Decision

Create a bounded Admin Publication Operations workspace backed only by the existing `ContentAuthoringService`, `SecuredContentAuthoringService`, `ContentAuthoringRepository`, publication registry/resolver, Admin session/CSRF policy, and append-only lifecycle audit.

### Canonical authority

- `ContentAuthoringService.publish` remains the only publication command.
- `ContentAuthoringService.withdraw` remains the only withdrawal command.
- Published `CaseVersion` remains immutable.
- Publication continues to atomically pin the active Content Configuration and exact resolved Flow provenance.
- The new router and UI are adapters; they do not reproduce lifecycle logic.

### Bounded queue and detail

Expose deterministic bounded queues for exactly two lifecycle states:

- `APPROVED`, for publication candidates;
- `PUBLISHED`, for withdrawal candidates.

Queues use `created_at DESC, id DESC`, bounded `limit`/`offset`, and optional exact `content_risk` and `primary_domain_code` filters. Detail loading is exact-ID and read-only. Queue and detail reads require `AUDIT_READ`; they never mutate state and never require browser persistence.

### Publication preflight

Expose an explicit read-only preflight command for an `APPROVED` CaseVersion.

Preflight:

1. runs the same canonical publication registry validation used by publish;
2. if structurally valid, resolves the exact current publishable Content Configuration and Flow provenance;
3. returns eligibility, bounded validation failures, and the prospective pinned provenance;
4. performs no lifecycle transition, persistence write, audit append, configuration mutation, or consumer-runtime mutation.

Preflight is advisory. It does not reserve state or provenance. The final publish command must re-run authoritative validation and resolution atomically so a stale preflight can never bypass current rules.

### Publish command

Publishing requires all of the following:

- exact `APPROVED` state;
- `CONTENT_PUBLISH` capability;
- recent step-up authentication under the existing Admin policy;
- same-session CSRF;
- an explicit `acknowledge_immutable: true` request field;
- an existing latest `approve` lifecycle audit entry;
- publisher actor different from the latest approving reviewer actor;
- canonical publication validation and provenance resolution succeeding at command time.

The command transitions only `APPROVED → PUBLISHED`. It does not create or edit content, approve review, publish Content Configuration, activate providers, or mutate unrelated CaseVersions.

### Withdraw command

Withdrawal requires:

- exact `PUBLISHED` state;
- `CONTENT_WITHDRAW` capability;
- recent step-up authentication;
- same-session CSRF;
- a non-empty bounded rationale.

The command transitions only `PUBLISHED → WITHDRAWN` and appends the rationale to the canonical lifecycle audit. It does not delete the immutable published version or automatically create a revision.

### Maker-checker policy

Extend the existing Admin security policy with `publisher_must_differ_from_approver = true` by default. Separation is enforced from the latest canonical `approve` audit actor, not from UI state or client-supplied identity.

The existing submitter-versus-reviewer separation remains unchanged.

### Admin UI

Add `/publication-operations` to Admin Studio.

The UI:

- starts no request on mount;
- uses explicit session, queue, detail, preflight, audit and decision commands;
- never stores session or CSRF values in `localStorage` or `sessionStorage`;
- shows APPROVED and PUBLISHED queues separately;
- presents CaseVersion content read-only;
- requires an explicit immutability acknowledgement before publish;
- requires a non-empty rationale before withdraw;
- shows preflight as advisory and never treats it as a reservation;
- exposes no edit, submit, approve, reject, configuration publish/rollback, bulk mutation or automatic action.

### API surface

The bounded adapter uses:

- `GET /internal/admin/v1/publication-operations`
- `GET /internal/admin/v1/publication-operations/{version_id}`
- `GET /internal/admin/v1/publication-operations/{version_id}/preflight`
- `POST /internal/admin/v1/publication-operations/{version_id}/decision`

The decision request is a strict tagged shape:

- `PUBLISH` requires `acknowledge_immutable: true` and no rationale;
- `WITHDRAW` requires rationale and does not accept publication acknowledgement as a substitute.

### OpenAPI composition

Generate an isolated `0.19` additive overlay after the Flow Composer overlay. The predecessor Flow Composer overlay must remain exact after this later same-version surface is added. MVP treats Publication Operations as a separate non-MVP additive overlay; Global `0.20` composes it into the ordered `0.19` baseline.

## Consequences

### Positive

- Publication becomes inspectable and operator-safe without duplicating domain logic.
- The final maker-checker boundary extends beyond review into publication.
- Preflight improves operability while preserving command-time authority and concurrency safety.
- Existing immutable CaseVersion and provenance pinning rules remain intact.

### Costs

- Additional API/UI/OpenAPI/test surface is required.
- Publisher operations depend on trustworthy lifecycle audit continuity.
- Preflight cannot guarantee a later publish result because configuration or lifecycle state may change.

## Explicit exclusions

This ADR does not add:

- automatic publication or withdrawal;
- bulk publish/withdraw;
- content editing or review;
- Content Configuration publish/rollback;
- moderation operations;
- media upload/CDN management;
- provider activation;
- production deployment or release APK;
- human editorial CQB/usability acceptance;
- deployed SLO/load/observability evidence;
- operator-validated rollback or store compliance.
