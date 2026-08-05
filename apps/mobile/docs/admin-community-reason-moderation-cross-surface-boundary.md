# Admin Community Reason Moderation — Cross-surface Boundary

## Scope

The `/reason-moderation` Admin Studio workspace and its internal Admin API are operator-only surfaces. They advance CAP-066 without changing mobile or public Community Reason contracts.

## Consumer invariants

- Mobile/public Community Reason reads continue to use the existing canonical `CommunityReason.publicly_readable` rule.
- Only `NOT_REQUIRED` and `ALLOWED` reasons are publicly readable.
- `PENDING` and `BLOCKED` reasons remain absent from public snapshots.
- Reaction and report commands keep their existing consumer request/response contracts.
- No Admin queue, report aggregate, moderation rationale, Admin actor reference or audit record is exposed to consumer APIs.
- No author or reporter actor identity is added to an Admin response or consumer response.

## Runtime isolation

- `CommunityReasonService.moderate()` remains the sole moderation decision authority.
- Admin queue/detail/audit responses are derived from the canonical repository and are not a second moderation store.
- Successful decisions change only canonical moderation state and append an immutable operator audit record.
- No mobile feature flag, navigation, copy, analytics event, local fixture or preview fallback is introduced by this slice.

## Evidence interpretation

Mobile CI, MVP Beta and Global Readiness runs on this branch prove only regression and compilation of the unchanged consumer surface. Any generated APK or phone-preview artifact is CI evidence, not a production or user release.

## Explicitly unproven

This repository slice does not prove human moderator usability/CQB, production policy quality, provider readiness, deployed SLO/load/observability, operator rollback, store compliance or production release readiness.
