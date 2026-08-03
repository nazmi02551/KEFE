# ADR-0092: Immutable dual-control public feed activation approval ledger

- Status: Accepted
- Date: 2026-08-03
- Slice: 56

## Context

Slice 55 records an immutable activation manifest and explicitly states that cataloging is not approval. A future provider activation requires two different governance questions to be answered independently: whether the source and technical configuration are verified, and whether the operational/editorial risk is acceptable. A generic mutable approval flag or a single reviewer would collapse those duties and make later audit reconstruction unreliable.

## Decision

KEFE introduces an immutable `PublicFeedActivationApprovalDecision` ledger with exactly two review kinds:

- `SOURCE_VERIFICATION`
- `RISK_REVIEW`

Each review records exactly one `APPROVED` or `REJECTED` decision and binds the exact catalog entry UUID, activation code and configuration hash. It stores only a bounded rationale code, an opaque evidence reference, a versioned policy code, the canonical Admin reviewer reference and a UTC decision time. Free-form rationale, secret values and mutable activation controls are excluded.

The repository is insert-only. It exposes create-or-get, exact lookup and deterministic listing. Exact re-recording by the same actor with the same immutable decision content is idempotent. Reusing a review kind with different content fails closed. UPDATE and DELETE are rejected in memory contracts, repository APIs and PostgreSQL triggers.

Dual control is mandatory. The Admin actor who records `SOURCE_VERIFICATION` cannot record `RISK_REVIEW` for the same activation, regardless of whether either decision is approval or rejection. PostgreSQL enforces this rule with an insert trigger in addition to service-layer validation.

Readiness is descriptive and deterministic:

- any recorded rejection -> `REJECTED`;
- two approvals from distinct actors -> `APPROVED`;
- otherwise -> `PENDING`.

`SOURCE_VERIFICATION` writes require `SOURCE_VERIFY`; `RISK_REVIEW` writes require `RISK_REVIEW`. Both use the existing authenticated Admin write principal, CSRF validation and step-up enforcement. Readiness inspection requires `SOURCE_VERIFY`.

Admin HTTP is explicit rather than generic:

- `GET /internal/admin/v1/public-feed-activations/{activation_code}/approval`
- `POST /internal/admin/v1/public-feed-activations/{activation_code}/source-verification`
- `POST /internal/admin/v1/public-feed-activations/{activation_code}/risk-review`

No generic approval edit, delete or activation endpoint is introduced.

## PostgreSQL

Migration `20260803_0027`, based on `20260803_0026`, creates an immutable approval table. A composite foreign key binds each decision to the exact catalog entry UUID, activation code and configuration hash. Unique constraints allow one decision per review kind. Database triggers reject same-actor cross-kind review and any UPDATE or DELETE. Downgrade is blocked while approval decisions exist.

## Production boundary

Production starts with an empty approval ledger. It does not seed decisions, build an activation bundle, install a schedule, register an adapter or worker, perform capture or publish content. Even `APPROVED` readiness is governance evidence only and does not activate a feed.

## Consequences

Approval history is reconstructible and duties remain separated. A later activation runtime must consume a separately designed, explicit activation command and cannot infer permission merely from catalog presence or bypass the dual-control ledger.