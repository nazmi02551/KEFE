# ADR-0100 — Secured Admin Studio Editorial Workspace

- **Status:** Accepted for implementation
- **Date:** 2026-08-04
- **Issue:** #296
- **Parent runtime:** PR #295 / `8166bcc72712e06e1b7705d3bf2e8b9dcbc1fa7b`
- **Capabilities:** CAP-061, CAP-062, CAP-063, CAP-065, CAP-095, CAP-126

## Context

The canonical backend now exposes an explicit human-controlled editorial lifecycle:

`Proposal queue → terminal Proposal review → accepted Source Brief → Candidate Bundle → independent dependency reviews → explicit Editorial Projection → Content Authoring DRAFT`.

`apps/admin` is only a placeholder. Operators must currently exercise the lifecycle through raw HTTP calls. That is not a bounded, reviewable or accessible Admin operation surface and encourages accidental coupling between actions that the domain deliberately keeps separate.

## Decision

Create the first production-shaped Admin Studio vertical slice as a standalone Next.js/TypeScript application under `apps/admin`.

The application is an API client and workflow presentation layer only. The API remains the sole source of truth for authorization, lifecycle state, lineage validation, idempotency and mutation outcomes.

### 1. Security boundary

- Admin authentication uses the existing `kefe_admin_session` cookie.
- Reads use same-origin credentialed requests.
- Every write requires an explicit operator-provided same-session `X-KEFE-CSRF` token.
- Missing API base URL, missing CSRF token or unauthenticated session fails closed.
- The client never stores Admin session cookies, credentials, secrets, raw evidence bodies or backend object keys.
- Error rendering is bounded and never injects response HTML.

### 2. Workspace boundary

The initial workspace contains four explicit operator stages:

1. **Queue** — filter and page through Proposals; select one record.
2. **Review** — inspect bounded Proposal metadata/payload and submit one terminal review decision.
3. **Bundle** — for an independently accepted `SOURCE_BRIEF`, submit immutable editorial configuration and receive exactly three review-required Proposal identities.
4. **Projection** — only after the `CANDIDATE_CASE` and required dependency Proposals are independently accepted, explicitly project to one Content Authoring `DRAFT`.

Stage navigation never performs a mutation. No action runs on mount, selection, navigation, refresh or polling.

### 3. No second CMS

The workspace does not create a parallel Case model, authoring lifecycle, Flow authority or publication mechanism. It only invokes existing canonical endpoints and displays returned identities/states.

Authoring submit, review, approval, publication, visual Case Builder, Flow Composer, provider activation and raw evidence viewing are excluded from this slice.

### 4. Idempotency

Editorial Projection requires an explicit idempotency key. The client derives a stable key from the selected candidate Proposal and review decision and keeps it stable across retry until the operator changes the selected lineage. The key is visible and editable before submission.

Candidate Bundle replay relies on the backend's immutable configuration hash and exact source/review identity. The client does not silently alter configuration on retry.

### 5. Accessibility and low-end performance

- Semantic headings, form labels, tables/lists and status text are required.
- Keyboard focus is visible and logical.
- Mutations expose pending, success and error states through `aria-live` regions.
- Motion is limited to nonessential CSS transitions and disabled under `prefers-reduced-motion`.
- No WebGL, canvas, continuously rendered animation or heavy component framework is introduced.
- The layout remains usable on narrow screens without hiding lifecycle or security information.

### 6. Testing and delivery

The repository must contain:

- executable contract `docs/contracts/admin-studio-editorial-workspace.v1.json`;
- an architecture checker proving security/no-automatic-mutation/no-publication boundaries;
- typed API client tests;
- component tests for queue, review, bundle and projection behavior;
- a deterministic mocked vertical journey;
- production Next.js build evidence in a dedicated Admin Studio CI workflow.

API CI, Mobile CI, MVP Beta Gates and Global Readiness remain required on the exact child head because the child becomes the canonical stack top, even though mobile behavior is unchanged.

## Consequences

### Positive

- The existing backend lifecycle becomes operable without weakening domain separation.
- Maker-checker and explicit-command semantics are visible in the product surface.
- The Admin application gains an independently testable delivery boundary.
- Future Case Builder and Flow Composer work can extend one canonical Admin Studio instead of creating another CMS.

### Costs and limitations

- This slice does not prove human editorial usability or CQB acceptance.
- It does not provide login issuance, production deployment, provider readiness, deployed SLO, rollback or store evidence.
- API payload changes require deliberate client contract updates.

## Rejected alternatives

1. **Combine review, bundle and projection into one action.** Rejected because it violates terminal independent review and explicit projection boundaries.
2. **Persist Admin workflow state in a parallel backend.** Rejected because the canonical API already owns state and idempotency.
3. **Use local fixtures as production fallback.** Rejected because Preview/production isolation is invariant.
4. **Build a visual Case/Flow editor in the same slice.** Rejected because it would exceed the bounded operational workspace and reopen authoring authority.
