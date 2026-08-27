# Public CaseVersion History — 2026-08-27

Status: IMPLEMENTATION CANDIDATE / EXACT-HEAD CI PENDING / NO CAPABILITY PROMOTION

Issue: #376

Capabilities: CAP-072 (primary), CAP-026 and CAP-095 (supporting)

Stack base: PR #375 / `feature/mvp-kefe-today-discovery` exact-green head
`ef3378b9263db1db044386ce795fe15df8528f1a`.

ADR: ADR-0134

Contract: `docs/contracts/public-case-version-history.v1.json`

## Why this slice exists

KEFE already retains immutable consumer CaseVersions when a later version is
published, but the reader could see only the active version. This slice exposes
that existing public history without treating every superseded version as a
correction and without projecting editorial drafts, reviewers, commands or
rationales into the consumer boundary.

## Candidate boundary

This slice:

- adds bounded `GET /v1/cases/{case_id}/history` projection with a maximum of
  20 records ordered by `version_no DESC`;
- requires an active published Case and returns only consumer CaseVersions whose
  exact status is `PUBLISHED` or `SUPERSEDED`;
- exposes only id, version number, title, summary, optional publication time and
  exact `CURRENT` / `PREVIOUS` classification;
- returns `CASE_NOT_FOUND` for empty, withdrawn or never-published Case history;
- adds memory and PostgreSQL repository evidence, including exclusion of draft
  and withdrawn records;
- adds a strict mobile parser that rejects empty, duplicated, reordered,
  malformed or unknown-classification responses;
- presents localized English and Turkish read-only history in both canonical
  Case journeys;
- keeps history failure independently retryable and non-blocking for Context,
  Weigh and Commit;
- allows Product Preview to project only its current fixture and forbids a
  synthetic previous version.

## Preserved boundaries

- A previous public version is not labelled as a correction.
- No source correction reason or verification methodology is inferred.
- Editorial actors, review records, commands and rationales remain private.
- Blind First, Commit First and immutable published CaseVersion behavior remain
  unchanged.
- No format-specific engine or KEFE Today-specific history path is introduced.
- Product Preview remains isolated from connected/production composition.

## Verification state

Local candidate evidence currently includes the full API test package, Ruff,
the committed OpenAPI check, production-runtime and contract-sync checks, and
the executable source/contract validator. PostgreSQL service-backed tests are
skipped in this local environment. Canonical Flutter format/analyze/tests,
PostgreSQL integration and exact-head API CI, Mobile CI, MVP Beta Gates and
Global Readiness remain pending until recorded against the final published
head.

APK handling follows the project evidence policy. The existing mobile CI may
produce an installable artifact for the final exact head, but this bounded trust
surface is not by itself a reason to distribute another APK.

## Non-claims

This checkpoint does not claim a correction workflow, source correction
history, human editorial acceptance, live production content, production
reachability, store readiness, human usability or capability lifecycle
promotion. `docs/status/CURRENT.md` is not advanced by this draft child slice.
