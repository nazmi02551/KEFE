# My KEFE Personal Journey Report — 2026-08-29

Status: IMPLEMENTATION CANDIDATE / LOCAL API VERIFIED / MOBILE CI PENDING  
Issue: #387  
Capability: CAP-120 (bounded first vertical; no lifecycle promotion)  
Stack parent: PR #386 / `ea9bcf9ecafd3db3b3654bd4163053427014d6f7`

ADR: ADR-0138  
Contract: `docs/contracts/my-kefe-journey-report.v1.json`

## Product value

My KEFE already summarized counts and recent Case journeys, but it did not let
the person review their own recorded decision moments as one chronological
experience. This candidate adds a directly reachable personal journey report
that is visible in both production composition and Product Preview.

The report presents:

- initial Commit moments;
- later decision-revision moments;
- Reflection-completion moments;
- a bounded observed summary and date range;
- canonical Case re-entry from every moment.

## Runtime boundary

The existing authenticated `GET /v1/me/progress` response gains an additive
`personal_report` member with at most 24 newest-first moments. Memory and
PostgreSQL reconstruct the report from canonical decision/reflection records on
read. No table, migration, analytics dependency or duplicated retention path is
introduced.

The API never returns the actor/session/revision/completion identifiers used for
ownership and deterministic ordering. It also returns no response, private
reason, DecisionDelta, Exposure/Intervention metadata, profile, score, rank,
causal explanation, Signal or Impact field.

## Phone surface

- shared route: `/my-kefe/report`;
- entry: My KEFE personal-report card;
- exit into product journey: canonical `/case/:caseId`;
- shared production/Product Preview screen;
- deterministic Preview moments supplied only by `PreviewProgressRepository`;
- strict missing-member compatibility and fail-closed malformed-member parsing;
- Turkish/English and light/dark coverage;
- explicit Preview and non-inference notices.

The Preview fixture is phone-review data only and is never a production
fallback.

## Local evidence

- full API Ruff: PASS;
- full API unit/behavior package: PASS (PostgreSQL opt-in tests skipped locally);
- focused empty, initial Commit and full Commit → revision → Reflection report
  assertions: PASS;
- My KEFE journey report executable contract: PASS;
- composed OpenAPI drift and contract-sync: PASS;
- production API runtime composition: PASS;
- capability portfolio validator: PASS;
- migration chain unchanged at `20260829_0041`.

Flutter SDK is not installed in the current local execution environment.
Formatting, analyzer, widget regressions, Android compile and installable
Preview artifact remain exact-head CI evidence and are not claimed locally.

## Required exact-head evidence

The final candidate must pass API CI, Mobile CI, MVP Beta Gates and Global
Readiness on one exact SHA. Because this is a meaningful phone-visible slice,
the installable Product Preview APK may be handed off only after those workflows
finish and its artifact identity and SHA-256 are recorded.

## Non-claims

This candidate does not complete or promote CAP-120/Chronicle/Wrapped, F5,
analytics reporting or production readiness. CI cannot prove human usability,
store readiness, provider delivery or deployed SLO.
