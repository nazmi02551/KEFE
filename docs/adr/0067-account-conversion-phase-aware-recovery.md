# ADR-0067 — Account conversion phase-aware recovery

**Status:** Accepted for Slice 29 implementation  
**Date:** 2026-08-01  
**Issue:** #167  
**Parent:** PR #165 / Slice 28

## Context

The optional account-conversion flow currently represents request, OTP verification and guest-history merge through one coarse error state. `AccountController.retry()` resets the flow to identifier entry regardless of the failed operation. Consequently:

- request failure loses the meaning of retry and requires another manual submit;
- OTP verification failure hides the existing challenge/code-entry phase;
- a successful OTP verification followed by merge failure discards the verified context and forces an unnecessary OTP restart;
- the presentation cannot distinguish verifying from merging.

This is a recovery-integrity defect, not a change to account eligibility, OTP policy, API semantics or guest-history ownership.

## Decision

Introduce phase-aware recovery inside the existing mobile account boundary.

1. Add explicit operation/failure phases for `requestOtp`, `verifyOtp` and `mergeGuest`.
2. Add a distinct `merging` UI state.
3. Preserve channel and identifier after request failure.
4. Preserve `OtpChallenge` after verification failure and return retry to code entry.
5. Hold a successful `OtpVerification` only in private `AccountController` memory while merge is pending or retryable.
6. On merge failure, retry `mergeGuest` directly with that in-memory verification token. Do not request or verify another OTP unless the verified context is unavailable.
7. Guard duplicate request, verify and merge actions.
8. Present deterministic, semantic operation and error surfaces with stable keys and governed EN/TR copy.

## Security boundary

The verification token:

- is controller-private and in-memory only;
- is not added to `AccountState`;
- is not persisted, serialized, logged, copied to clipboard or exposed to widgets;
- is cleared on successful conversion, new OTP request and full reset/fallback.

This ADR does not claim production OTP/provider deliverability or token-revocation behavior beyond the existing repository/API contract.

## Preserved boundaries

- `AccountRepository` method signatures and HTTP endpoints;
- account-offer eligibility and placement;
- guest continuation;
- actor/history merge semantics;
- credential-store behavior;
- production/Product Preview provider isolation;
- routes, API schema, migrations and server state;
- no personality, ideology, psychometric, bias, causal, normative, Signal or Impact inference.

## Consequences

Positive:

- errors are recoverable from the correct phase;
- successful OTP verification is not repeated solely because merge failed;
- UI communicates verification and merge as different operations;
- duplicate actions are bounded at controller level.

Trade-offs:

- controller owns a short-lived private verification object;
- retry behavior is operation-specific rather than one generic reset;
- an unavailable/expired verified context falls back to code entry rather than pretending merge can continue.

## Evidence requirement

Slice 29 is PASS only when the exact runtime SHA succeeds in API CI, Mobile CI, MVP Beta Gates and Global Readiness, including executable contract guards, controllable-repository recovery tests, compact/enlarged-text theme tests and phone-candidate reachability.