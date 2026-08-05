# ADR-0105: Bounded Admin Community Reason Moderation Operations

- Status: Accepted for implementation
- Date: 2026-08-05
- Parent runtime: PR #305 at `9342989bf76b22036501f7792d1adb5ffb309f8b`
- Primary capability: CAP-066 Reason/Content Moderation Operations
- Supporting capability: CAP-126 Admin Studio

## Context

KEFE already has one Community Reason domain. A committed weigh session may publish structured reason tags and an optional short text. Tag-only reasons are `NOT_REQUIRED`; text reasons enter `PENDING`; public reads expose only `NOT_REQUIRED` and `ALLOWED`. Users may react and may report a reason with one of the canonical report codes. The existing internal moderation endpoint can set `ALLOWED` or `BLOCKED`, but the domain has no bounded operator queue, no privacy-safe report context, no append-only moderation audit and no dedicated moderation capability.

F3 requires moderation and audit to be operable. Creating another moderation model, copying Community Reason content into an Admin-only store, or exposing reporter identities would break the existing authority and privacy boundaries.

## Decision

### 1. One moderation authority

`CommunityReasonService.moderate()` remains the only Community Reason moderation decision command. The new Admin router and Admin Studio page are bounded adapters. They do not implement a second moderation state machine, public-reason store, report store or consumer read path.

The service delegates one atomic repository command that locks the current reason, validates the allowed source state, writes the resulting moderation state and appends the audit record in the same transaction.

### 2. Moderation candidates

Two explicit queue kinds are supported:

- `PENDING`: text-bearing reasons whose moderation state is `PENDING`.
- `REPORTED`: publicly readable `NOT_REQUIRED` or `ALLOWED` reasons with at least one report newer than their latest moderation audit decision.

`BLOCKED` reasons are never active queue candidates. They remain available by exact ID for inspection and audit.

Queue ordering is deterministic and oldest-first by the candidate timestamp, then reason ID. `PENDING` uses `created_at`; `REPORTED` uses the latest report timestamp. Pagination is bounded by `limit` 1..100 and `offset` 0..10000. Optional exact filters may narrow by `case_version_id` and canonical `report_code`.

### 3. Privacy-safe inspection

Admin queue and detail responses expose:

- reason ID and CaseVersion ID;
- tags, optional body and moderation state;
- created/updated timestamps;
- total reports, counts by canonical report code and latest report timestamp.

They never expose the Community Reason author actor ID, weigh session ID, reporter actor IDs, reporter ordering, account details, device data or inferred user attributes. Report identities remain repository-internal uniqueness keys only.

### 4. Explicit decisions and audit

The bounded decision endpoint accepts only `ALLOWED` or `BLOCKED` plus a trimmed human rationale between 10 and 1000 characters.

Allowed source states are:

- `PENDING → ALLOWED` or `PENDING → BLOCKED`;
- `NOT_REQUIRED → ALLOWED` or `NOT_REQUIRED → BLOCKED` for reported tag-only reasons;
- `ALLOWED → ALLOWED` to uphold a newly reported public reason, or `ALLOWED → BLOCKED`.

`BLOCKED` is terminal in this slice. Unblock, appeal and restore are excluded.

Every successful decision appends an immutable audit record containing a server-generated audit ID, reason ID, server-derived Admin actor reference, previous state, decided state, rationale and timestamp. An uphold decision may keep the state `ALLOWED`; the new audit timestamp resolves only reports that existed before that decision. A later report makes the reason a candidate again.

The existing compatibility endpoint remains in place to preserve the additive OpenAPI invariant. It is moved onto the same `CONTENT_MODERATE` capability, recent step-up, CSRF, state validation and atomic audit command. It reads an explicit `X-KEFE-Moderation-Rationale` request header directly without changing its existing OpenAPI request schema; missing or invalid rationale fails closed. It cannot bypass the bounded service rules.

### 5. Admin security

A dedicated `CONTENT_MODERATE` capability is added and granted to the Reviewer role. It is a recent-step-up capability.

- queue and exact detail require `CONTENT_MODERATE`;
- audit read requires `AUDIT_READ`;
- decisions require `CONTENT_MODERATE`, same-session CSRF and recent step-up;
- the Admin actor reference always comes from the authenticated server-side principal.

The browser never supplies actor IDs or authorization claims.

### 6. Admin Studio behavior

`/reason-moderation` provides separate `PENDING` and `REPORTED` queues. Route load, query prefilling, filter changes and item selection start no request. Session submission, queue load, detail load, audit load and decision submission are separate explicit commands.

The workspace is read-only except for one explicit moderation decision. Changing the selected reason, detail, queue kind, rationale or decision clears confirmation. No autosave, local storage, session storage, polling, bulk action or automatic moderation is allowed.

### 7. OpenAPI composition

The surface is an additive same-version `0.19` overlay composed after Publication Operations. Its generator must fail if any predecessor path or schema changes, disappears or is absorbed. Publication Operations remains an exact independent predecessor overlay.

### 8. Cross-surface boundary

Consumer and mobile Community Reason contracts do not change. Public visibility continues to be derived only from the canonical moderation state. Admin CI phone artifacts are regression/compile evidence, not a release.

## Consequences

- Moderators gain a deterministic operational queue and privacy-safe report evidence.
- Decisions become attributable and durable without leaking reporter identities.
- Existing public reason behavior and the single moderation command remain authoritative.
- PostgreSQL requires an append-only moderation audit table and indexed queue queries.
- The compatibility endpoint becomes stricter at runtime while its existing OpenAPI request schema remains unchanged.

## Explicit exclusions

- automatic, model-assisted or bulk moderation;
- content rewriting or editing;
- reporter or author identity disclosure;
- user reputation, trust score, personality, ideology, bias or causal inference;
- appeal, unblock, restore or deletion workflows;
- moderation of Cases, sources, media or provider output;
- media pipeline work under CAP-067;
- provider activation, production deployment or release APK;
- claims of human CQB/usability, deployed SLO/load/observability, rollback, store compliance or production readiness.
