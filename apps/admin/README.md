# KEFE Admin Studio

Next.js editorial and operational control plane. Admin capabilities use the canonical API and domain terminology; the UI never creates a parallel CMS, lifecycle or publication authority.

## Current vertical slice

The first secured workspace exposes four separate operator stages:

1. Proposal queue and bounded filters;
2. Proposal detail and terminal human review;
3. accepted Source Brief to review-required Candidate Bundle;
4. independently accepted Candidate Case to Content Authoring DRAFT projection.

Review, bundle creation and projection are explicit independent actions. The workspace does not submit, approve or publish authoring content.

## Local setup

```bash
cp .env.example .env.local
npm install
npm run dev
```

`NEXT_PUBLIC_KEFE_API_BASE_URL` must point to the canonical API. HTTPS is required outside `localhost`.

The existing Admin session is supplied by the `kefe_admin_session` cookie. Every write additionally requires a same-session CSRF token entered into the workspace and sent as `X-KEFE-CSRF`. The token remains in page memory and is not persisted by the application.

## Verification

```bash
npm run verify
```

This runs the executable architecture contract, ESLint, strict TypeScript, API/component/vertical tests and a production Next.js build.

Automated checks do not prove human editorial usability, CQB acceptance, production deployment, provider readiness, deployed SLO or operator rollback.
