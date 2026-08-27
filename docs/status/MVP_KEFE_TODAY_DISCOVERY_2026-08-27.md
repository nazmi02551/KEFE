# MVP KEFE Today Discovery — 2026-08-27

Status: IMPLEMENTATION CANDIDATE / EXACT-HEAD CI PENDING / NO CAPABILITY PROMOTION

Issue: #373

Capabilities: CAP-026 (primary), CAP-095 (supporting)

Stack base: PR #374 / `feature/f4-session-renewal-convergence` exact-green head
`490020778f6e1751753cac730376d589f1062afd`.

ADR: ADR-0133  
Contract: `docs/contracts/kefe-today-real-event-projection.v1.json`

## Why this slice exists

KEFE Today could not be truthfully surfaced from the existing mobile summary.
The source authoring model already contained reviewed `is_real_event` metadata,
but consumer materialization discarded it. Inferring a real event from CIVIC,
domain, title, freshness or list order would convert presentation heuristics
into an unsupported editorial claim.

## Candidate boundary

This slice:

- adds linear migration `20260827_0037` with a safe `false` default;
- copies the exact authoring boolean into immutable consumer CaseVersion;
- projects it through Decision repositories and `GET /v1/cases`;
- parses absent/invalid mobile metadata as `false` and only exact JSON `true` as
  eligible;
- selects the first eligible Case without changing server ordering;
- adds localized EN/TR KEFE Today content and a canonical Case CTA;
- shows a localized, non-actionable empty state when no governed Case exists;
- leaves existing Product Preview cases false rather than inventing a real-event
  fixture.

The existing content-configuration policy continues to require
`SOURCE_VERIFICATION` for real-event content. This slice does not establish a
second classification path.

## Preserved boundaries

- KEFE Today reuses `/case/:caseId`; no format-specific engine is added.
- Blind First and Commit First remain in the canonical Case journey.
- No client freshness threshold or ordering rule is introduced.
- No inference uses format, domain, title, summary, risk or list position.
- Product Preview and connected/production compositions remain isolated.
- No result, Signal or social consensus claim is added.

## Planned evidence

- executable source/contract validator in both existing core CI surfaces;
- API unit/OpenAPI/production-runtime and PostgreSQL integration gates;
- content publication projection and migration-chain coverage;
- mobile format/analyze, strict parser and Experience Hub regressions;
- exact-head API CI, Mobile CI, MVP Beta Gates and Global Readiness.

APK handling follows the project evidence policy. An installable artifact may be
recorded if CI naturally produces one, but Product Preview intentionally shows
the truthful empty Today state, so an APK is not distributed merely as feature
proof.

## Non-claims

This checkpoint does not claim exact-head PASS, human review, merged runtime,
live real-event inventory, source freshness, production reachability, store
readiness or CAP-026/CAP-095 lifecycle promotion. `docs/status/CURRENT.md` is not
advanced by this draft child slice.
