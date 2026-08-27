# ADR-0133 — Governed real-event metadata powers KEFE Today

Status: IMPLEMENTATION CANDIDATE  
Date: 2026-08-27  
Issue: #373  
Capabilities: CAP-026 (primary), CAP-095 (supporting)  
Parent: PR #374 / `490020778f6e1751753cac730376d589f1062afd`

## Context

The authoring aggregate already records `AuthoringCaseVersion.is_real_event`,
and the content-configuration policy requires `SOURCE_VERIFICATION` for every
fact-bearing or real-event Case. That reviewed metadata is currently discarded
when a published authoring version is materialized into `content.case_version`.
Consequently the consumer API and mobile client cannot identify a real-event
Case without guessing from title, domain, format, publication time or list
position.

Those guesses are not trustworthy. A CIVIC Case is not necessarily current, a
recently published Case is not necessarily about a real event, and a real-event
Case is not necessarily CIVIC.

## Decision

The canonical consumer projection will carry the exact governed boolean:

1. `content.case_version.is_real_event` is a non-null boolean with a `false`
   default for existing and legacy rows;
2. publication materialization copies
   `AuthoringCaseVersion.is_real_event` without inference or recomputation;
3. Decision repositories expose the field on immutable `CaseVersion`;
4. `GET /v1/cases` includes `is_real_event` on each summary;
5. mobile treats only JSON boolean `true` as real-event metadata and treats an
   absent, null or non-boolean value as `false`;
6. KEFE Experiences selects the first real-event Case in the server's existing
   Explore order and opens the canonical `/case/:caseId` journey;
7. when no summary is explicitly real-event, KEFE Today is a localized,
   non-actionable empty state.

The server remains the ordering authority. This slice adds no client freshness
threshold and does not reorder the Explore response.

## Editorial and truthfulness boundary

This projection does not create a new way to classify content. The existing
content-configuration rule remains authoritative: real-event content requires
`SOURCE_VERIFICATION`, and publication remains subject to the normal lifecycle
and review gates.

The mobile client must not infer KEFE Today eligibility from:

- `base_format` or `primary_domain` (including CIVIC values);
- title, summary, source wording or keywords;
- risk level;
- publication timestamp or perceived freshness;
- position in the Explore list.

Product Preview does not acquire a synthetic real-event fixture. Its existing
representative cases therefore exercise the truthful empty state until a
separately governed Preview fixture is explicitly approved.

## Preserved architecture

- KEFE Today is discovery, not a Today-specific decision engine;
- the CTA enters the existing generic Case journey;
- Blind First and Commit First remain enforced there;
- published CaseVersion remains immutable;
- Product Preview and connected/production compositions remain isolated;
- no result, collective opinion, Signal or freshness claim is introduced.

## Schema and compatibility

Migration `20260827_0037` extends the existing linear Alembic chain. The
database default and model/client defaults are `false`, so old rows and older API
payloads remain safe and do not become eligible by accident.

## Evidence

The executable contract `kefe-today-real-event-projection.v1.json`, its source
validator, API/PostgreSQL tests and mobile widget/parser tests bind this boundary
to the existing API and Mobile CI gates. No dedicated workflow is introduced.

## Non-claims

This ADR does not assert that any current Product Preview Case is a real event,
that a Case is fresh, that external sources are live, or that CAP-026/CAP-095 has
been lifecycle-promoted. Human review and exact-head CI remain separate gates.
