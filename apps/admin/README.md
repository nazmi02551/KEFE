# KEFE Admin Studio

Next.js editorial and operational control plane. Admin capabilities use the canonical API and domain terminology; the UI never creates a parallel CMS, lifecycle or publication authority.

## Editorial operations workspace

The first secured workspace exposes four separate operator stages:

1. Proposal queue and bounded filters;
2. Proposal detail and terminal human review;
3. accepted Source Brief to review-required Candidate Bundle;
4. independently accepted Candidate Case to Content Authoring DRAFT projection.

Review, bundle creation and projection are explicit independent actions. The workspace does not submit, approve or publish authoring content.

## Case Builder DRAFT workspace

`/case-builder` opens one exact canonical `AuthoringCaseVersion` through an explicit load command. A `?version=<uuid>` query parameter may prefill the ID but never starts a request on mount.

The Case Builder provides:

- structured core metadata, risk/fact flags, market/locale and review-mode editing;
- validated section editors for issues/questions, context blocks, source references and localizations;
- read-only Flow template identity and server-owned completed review modes;
- explicit DRAFT save through same-session CSRF;
- separately acknowledged DRAFT → IN_REVIEW submission;
- explicit append-only lifecycle audit loading;
- a dirty-state guard that prevents submitting unsaved browser changes.

It deliberately does not expose autosave, approve, reject, publish, withdraw, bulk mutation or Flow topology editing. Session and CSRF values remain in page memory and are never persisted by the application.

## Editorial Quality Review workspace

`/content-review` exposes a bounded queue of canonical `IN_REVIEW` CaseVersions. Loading the route, choosing a queue item or changing filters never starts a request automatically; session, queue, detail and audit reads each require an explicit operator command.

The workspace provides:

- reviewer-authorized queue filtering by content risk and primary domain;
- deterministic bounded pagination;
- salt-read-only CaseVersion inspection without edit authority;
- exact required review-mode attestation;
- maker-checker separated APPROVE to `APPROVED` without publication;
- rationale-bound REJECT to `DRAFT` with stale review attestations cleared;
- explicit append-only lifecycle audit loading.

It deliberately does not expose content editing, autosave, publish, withdraw, Flow topology changes, automated review or automated approval. Session and CSRF values remain in page memory and are never persisted by the application.

## Flow Composer DRAFT workspace

`/flow-composer` manages versioned generic Flow templates inside one exact canonical `ContentConfigurationSnapshot`. A `?version=<uuid>` query parameter only prefills the version ID; it never starts a request.

The workspace provides:

- an explicit clone-current command that creates a new configuration `DRAFT`;
- exact-ID loading for DRAFT or immutable historical versions;
- read-only Primitive and Capability catalogs with compatibility metadata;
- structured Flow Template and Step editing;
- accessible add, remove, move-up and move-down controls without a drag-and-drop dependency;
- deterministic text topology previews;
- client checks for identities, references, compatibility, reachability and cycles;
- explicit DRAFT save and exact-version audit loading;
- a dirty-state guard and explicit discard command.

Only `flow_templates` are submitted. The server reloads the canonical DRAFT and preserves taxonomies, risks, catalogs, modifier compatibility and every other non-Flow field. The workspace deliberately does not expose configuration publication, rollback, Case editing/review, autosave, automatic Flow generation or consumer-runtime mutation.

## Publication Operations workspace

`/publication-operations` exposes separate bounded queues for canonical `APPROVED` and `PUBLISHED` CaseVersions. A `?version=<uuid>` query parameter only prefills the exact ID. Route loading, queue selection, filter changes and confirmation changes never start a request.

The workspace provides:

- exact risk/domain filters and bounded deterministic pagination;
- explicit read-only detail and append-only lifecycle audit loading;
- an explicit advisory publication preflight that performs no persistence write or lifecycle transition;
- prospective Content Configuration and Flow provenance inspection;
- an explicit immutable-version acknowledgement before publish;
- same-session CSRF and recent server-enforced step-up for publish and withdraw;
- server-derived maker-checker separation between the latest approving reviewer and publisher;
- rationale-bound `PUBLISHED → WITHDRAWN` with immutable publication provenance retained.

Preflight never reserves lifecycle state or provenance. The final publish command repeats canonical validation and Flow/configuration resolution before atomically transitioning `APPROVED → PUBLISHED`. The workspace deliberately does not expose content editing, review decisions, Content Configuration publish/rollback, bulk publication, automatic actions, moderation or media operations.

## Local setup

```bash
cp .env.example .env.local
npm ci
npm run dev
```

`NEXT_PUBLIC_KEFE_API_BASE_URL` must point to the canonical API. HTTPS is required outside `localhost`.

The existing Admin session is supplied by the `kefe_admin_session` cookie. Every write additionally requires a same-session CSRF token entered into the workspace and sent as `X-KEFE-CSRF`.

## Verification

```bash
npm run verify
```

This runs all five executable Admin architecture contracts, ESLint, strict TypeScript, API/client/helper tests and a production Next.js build.

Automated checks do not prove human editorial usability, CQB acceptance, production deployment, provider readiness, deployed SLO/load/observability, operator rollback, store compliance or production release.
