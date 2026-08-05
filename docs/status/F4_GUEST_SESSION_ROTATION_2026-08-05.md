# F4 Guest Session Rotation — 2026-08-05

## Delivery identity

- Capability: `CAP-084`
- Foundation phase: `F4`
- Issue: #314
- Base SHA: `44a3e60e9681a1d0e781f887a758f28eae7a71e1`
- Branch: `feature/f4-guest-session-rotation`
- Decision: ADR-0109

## Implemented boundary

- First-time guest promotion revokes every pre-conversion guest session.
- Merge into an existing account revokes source guest sessions instead of reassigning them to the account actor.
- Existing destination-account sessions remain active.
- The newly issued account credential is the only credential returned by conversion.
- PostgreSQL preserves `REVOKED` classification even after the source guest actor is retired.
- Product history, share control, community ownership and actor-merge provenance remain intact.

## Verification boundary

The dedicated `Guest Session Rotation CI` workflow provides:

- focused Ruff validation;
- exact composed OpenAPI drift check;
- in-memory first-promotion and existing-account merge proof;
- MVP product-history proof;
- PostgreSQL migration, ownership-transfer and session-rotation proof.

Repository-wide CI remains required before this slice can be treated as exact-head verified.

## Explicitly not completed

- durable replay/idempotency after OTP verification consumption;
- full duplicate-side ownership resolution for every future product aggregate;
- participant-facing merge-conflict explanation UI;
- production OTP delivery and deployed identity SLO evidence.

CAP-084 remains `IMPLEMENTED_PARTIAL`.