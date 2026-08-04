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

This runs both executable architecture contracts, ESLint, strict TypeScript, API/client/helper tests and a production Next.js build.

Automated checks do not prove human editorial usability, CQB acceptance, production deployment, provider readiness, deployed SLO/load/observability, operator rollback, store compliance or production release.
