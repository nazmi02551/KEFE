# ADR-0106: Privacy-safe Admin Operational Reports Snapshot

- Status: Accepted for implementation
- Date: 2026-08-05
- Parent runtime: PR #307 at `6d5bc52388b590706a3a07aef9b2be08bc501aae`
- Primary capability: CAP-123 Admin Operational Reports
- Supporting capability: CAP-126 Capability Portfolio Register

## Context

KEFE already has authoritative operational facts distributed across existing domains:

- `ContentSupplyHealthService` derives source scheduling, dispatch, ingestion, Proposal and content-supply-cycle health from the existing operational repositories;
- `ContentAuthoringRepository` owns CaseVersion lifecycle state;
- `ProposalReviewQueueRepository` owns Proposal review-state reads;
- `CommunityReasonRepository` owns moderation queue eligibility and report-resolution semantics.

F3 requires Admin operational reports to be available. Creating a second analytics warehouse, event pipeline, reporting persistence model or copied operational state would create another source of truth and could silently diverge from the runtime authorities. Exposing individual content, actor, reporter, account or device records would also exceed the operational need and weaken privacy boundaries.

The Case media platform remains a separate capability because no canonical media/object-storage/CDN domain is yet present. This ADR does not invent provider, storage, licensing, CDN or media-lifecycle decisions.

## Decision

### 1. One read-only aggregate snapshot

A single explicit Admin read endpoint returns one server-generated operational snapshot:

`GET /internal/admin/v1/operational-reports/snapshot`

The endpoint is a bounded adapter over existing authorities. It does not persist a report, cache a report, copy operational records, create events, reserve work, mutate queues or acknowledge incidents.

One server `as_of` timestamp is created at command time and passed through the complete snapshot. Every section represents facts observed for that same logical instant. Repository-specific transaction timing may differ, so the response is an operational snapshot rather than a serializable cross-database audit statement.

### 2. Authoritative sections

The snapshot contains four aggregate sections:

1. `content_supply`: the existing `ContentSupplyHealthService.snapshot()` result and its transparent policy values;
2. `editorial_lifecycle`: exact counts for `DRAFT`, `IN_REVIEW`, `APPROVED`, `PUBLISHED`, `SUPERSEDED` and `WITHDRAWN` from `ContentAuthoringRepository`;
3. `proposal_review`: exact counts for `PENDING`, `ACCEPTED`, `REJECTED` and `CHANGES_REQUESTED` from `ProposalReviewQueueRepository`;
4. `moderation`: exact active-candidate counts for the existing `PENDING` and `REPORTED` Community Reason queue semantics.

New count methods may be added to those repository ports and implementations, but they must query the existing records and eligibility rules. They must not introduce a new report table or materialized aggregate.

### 3. Transparent signal, not a magic score

The snapshot exposes `overall_signal` with only `QUIET`, `NOMINAL`, `ATTENTION` or `CRITICAL`, plus sorted unique reason codes and the exact thresholds used.

- `CRITICAL` is emitted only when the authoritative content-supply signal is `CRITICAL`.
- `ATTENTION` is emitted when content supply is `ATTENTION`, or when an explicit operational backlog count exceeds its returned threshold.
- `QUIET` is emitted only when content supply is `QUIET` and every editorial, Proposal and moderation backlog is zero.
- otherwise the signal is `NOMINAL`.

The initial transparent backlog thresholds are:

- `in_review_attention_threshold = 50`;
- `pending_proposal_attention_threshold = 100`;
- `moderation_candidate_attention_threshold = 50`.

The reason codes identify the exact exceeded condition. No weighted score, ranking, prediction, recommendation or inferred production health is produced.

### 4. Privacy and payload minimization

The report exposes aggregate counts, explicit thresholds, operational signal/reason codes and timestamps only.

It never exposes:

- Case, CaseVersion, Proposal, reason, actor, author, reporter, session, account or device identifiers;
- titles, summaries, prompts, answers, reason text, rationales or source content;
- raw evidence, source locators, credentials, secrets, storage references or backend object keys;
- user segments, demographic attributes or individual activity;
- personality, ideology, psychometric, morality, bias, social-worth, causal or normative inference.

The report is not a user analytics surface and is not a research export.

### 5. Admin security

A dedicated `OPERATIONAL_REPORT_READ` capability is added. It is granted to `REVIEWER`, `PUBLISHER` and `ACCESS_ADMIN` because these roles operate the reviewed-content, publication and platform-control boundaries represented in the snapshot.

The endpoint requires an authenticated read principal and `OPERATIONAL_REPORT_READ`. It is GET-only, does not require CSRF and is not a recent-step-up capability. No browser-supplied actor, role, threshold or policy value is accepted.

### 6. Admin Studio behavior

`/operational-reports` is a read-only workspace.

Route loading, query prefilling, navigation and focus changes start no request. Session verification and snapshot loading are separate explicit commands. The workspace does not poll, auto-refresh, autosave or use local/session storage. It provides no acknowledgement, assignment, export, notification, remediation or mutation control.

Displayed thresholds and reason codes must remain visible so the signal is explainable. Static links to existing operational workspaces may be provided, but they must not trigger background reads or mutations.

### 7. OpenAPI composition

The surface is an additive same-version `0.19` overlay composed after Community Reason Moderation. Its generator emits exactly the one new path and transitively required schemas. The predecessor moderation overlay must remain exact and independent after this later same-version surface is added.

MVP treats Operational Reports as an independent non-MVP additive overlay. Global `0.20` composes it into the ordered pre-global `0.19` baseline.

### 8. Cross-surface and evidence boundary

Consumer and mobile contracts do not change. Repository snapshots and CI prove only deterministic repository-candidate behavior. They do not prove deployed monitoring, alert delivery, production SLOs, provider readiness, human operational acceptance or incident-response effectiveness.

## Consequences

- Admin operators gain a single explicit, privacy-safe overview of existing content supply, editorial, Proposal and moderation backlogs.
- Operational counts remain live projections of existing authorities rather than copied analytics state.
- Existing repository ports gain exact aggregate-count methods implemented consistently in memory and PostgreSQL.
- No migration is required for the report itself.
- CAP-094 media platform remains an independent future contract-first decision.

## Explicit exclusions

- report persistence, caching, scheduling, polling or notifications;
- analytics warehouse, event pipeline or materialized reporting tables;
- individual records, drill-down payloads or user/segment analytics;
- export, acknowledgement, assignment or remediation commands;
- automated editorial, moderation, publication or provider action;
- opaque score, prediction, recommendation or production-health certification;
- media/object-storage/CDN implementation;
- provider activation, production deployment or release APK;
- claims of human CQB/usability, deployed SLO/load/observability, incident response, rollback, store compliance or production readiness.
