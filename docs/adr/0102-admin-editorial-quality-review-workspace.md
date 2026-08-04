# ADR-0102 — Bounded Admin Editorial Quality Review Workspace

- **Status:** Accepted for implementation
- **Date:** 2026-08-04
- **Capabilities:** CAP-065 (primary), CAP-063 and CAP-126 (supporting)
- **Parent runtime:** PR #299 exact verified head `612c57fa2188c7f9c5fae8f64fcfebbca644cfbc`

## Context

PR #299 gives editors a bounded Case Builder that loads one canonical `AuthoringCaseVersion`, explicitly saves a DRAFT and separately submits it to `IN_REVIEW`. The existing Content Authoring domain already owns approve, reject, publish and lifecycle audit behavior, but Admin Studio has no reviewer-facing queue or read-only quality-review surface. The existing strict Admin routes also permit approval without an explicit review-mode attestation when a CaseVersion declares required review modes.

The next coherent boundary is therefore not Flow Composer or publication. It is an independent quality-review operation that completes the DRAFT → IN_REVIEW → APPROVED/DRAFT lifecycle without creating a second CMS or weakening maker-checker separation.

## Decision

Implement one additive Editorial Quality Review adapter and one Admin Studio review workspace.

### Review queue

The canonical Content Authoring repository gains a bounded state query for `IN_REVIEW` versions. The query:

- is reviewer-authorized;
- supports bounded `limit` and `offset` pagination;
- supports exact optional filters for content risk and primary domain;
- sorts deterministically by `created_at DESC, id DESC`;
- exposes no raw evidence body, credentials, secrets or backend object keys.

### Review detail

A reviewer may inspect one exact `IN_REVIEW` CaseVersion through a read-only adapter without receiving edit authority. The response includes the canonical authoring content, required/completed review modes, submitter audit identity and submission time. Audit remains append-only and is loaded explicitly.

### Review decision

One explicit write command accepts either `APPROVE` or `REJECT`.

For `APPROVE`:

- existing `CONTENT_REVIEW` authorization and maker-checker separation remain mandatory;
- the client must attest completed review modes;
- the server normalizes and validates the attestation;
- the attested set must exactly equal the CaseVersion's required review-mode set;
- unknown, duplicate, missing or extra modes fail closed;
- lifecycle transition and persisted completed modes occur atomically;
- approval does not publish.

For `REJECT`:

- a non-empty bounded rationale is mandatory;
- the version returns to DRAFT;
- completed review-mode attestations are cleared so a later resubmission cannot reuse stale review evidence;
- rejection does not edit content automatically.

The existing legacy approve command remains available for compatibility, but the domain now enforces the same required-review-mode completeness rule. It can therefore approve only versions with no required modes or versions whose completed modes were already validly established.

### Admin Studio

Add `/content-review` with:

- no request on mount;
- explicit session and queue loading;
- bounded filters and pagination;
- one selected read-only detail;
- visible required-mode checklist;
- explicit approve/reject choice;
- rationale required for rejection;
- same-session CSRF before any write reaches the network;
- no session/CSRF browser persistence;
- dirty/editor mutation controls absent;
- no publish, withdraw, Flow edit or automatic decision.

## Security and authority

- Existing `kefe_admin_session`, `X-KEFE-CSRF`, Admin capability policy and audit actor derivation remain authoritative.
- Content Authoring remains the sole Case/lifecycle authority.
- Reviewer reads require `CONTENT_REVIEW`; they do not imply `CONTENT_EDIT`.
- Approval remains maker-checker separated from the latest submitter.
- Browser errors are bounded and rendered as text.

## Consequences

Positive:

- Case Builder submissions become operationally reviewable.
- Required review modes become enforced evidence rather than editable metadata.
- Rejected content returns cleanly to DRAFT without stale attestations.
- Flow Composer and publication remain separate future slices.

Trade-offs:

- Repository ports gain a bounded cross-case state query.
- Same-version OpenAPI overlays require another isolated additive layer.
- Automated tests still do not prove human editorial quality or CQB acceptance.

## Explicit non-goals

This ADR does not implement publication, withdrawal, Flow Composer, visual drag-and-drop authoring, automated review, automated approval, provider activation, raw evidence viewing, production deployment, a release APK, human CQB acceptance, deployed SLO/load/observability, rollback validation or store compliance.
