# F4 Durable Guest Merge Replay — 2026-08-05

## Delivery identity

- Capability: `CAP-084`
- Foundation phase: `F4`
- Issue: #316
- Parent PR: #315
- Base SHA: `f75dd02f16ebb752339659b762cad95fd635355f`
- Branch: `feature/f4-guest-merge-replay`
- Decision: ADR-0110
- Contract: `docs/contracts/guest-account-merge-replay.v1.json`

## Implemented boundary

- The OTP verification-token hash is the natural replay identity for guest-account conversion.
- The exact account bearer is reconstructed through domain-separated HMAC-SHA-256.
- Plaintext account and verification credentials are never persisted.
- PostgreSQL completes verification consumption, actor promotion/merge, source-session revocation, account-session creation and replay persistence in one transaction.
- Exact retries return the same actor, bearer, expiry and merge provenance after response loss or application restart.
- Concurrent duplicate requests converge to one replay record and one account session.
- A revoked source bearer can retrieve only its matching completed replay and cannot start a new conversion.
- Replays are bound to the source actor; mismatches return `AUTH_MERGE_REPLAY_MISMATCH`.
- Public request and response schemas remain unchanged.
- Replay metadata is deleted through the verification-material privacy cascade.

## Verification boundary

The dedicated `Guest Merge Replay CI` provides:

- focused Ruff validation;
- executable architecture-contract verification;
- exact composed OpenAPI no-drift proof;
- in-memory exact replay, actor-binding, revoked-without-replay and concurrency evidence;
- PostgreSQL migration, restart, concurrency, single-session and no-plaintext persistence evidence;
- parent guest-session-rotation and MVP continuity regressions.

Repository-wide API, Privacy, MVP, Global and relevant dependency workflows remain required on the exact final head before the PR is review-ready.

## External and remaining gates

- `KEFE_ACCOUNT_MERGE_REPLAY_SECRET` requires stable secret-manager delivery and an explicit rotation procedure before production activation.
- Production OTP provider delivery, abuse controls, deployed observability/SLO and rollback evidence remain external gates.
- Broader duplicate-side ownership policies for future product aggregates and participant-facing merge-conflict explanations remain separate CAP-084 work.

CAP-084 remains `IMPLEMENTED_PARTIAL`; this slice does not claim production identity readiness.