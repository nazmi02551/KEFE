# ADR-0145 — Account conversion validation and recovery

Status: CANDIDATE  
Date: 2026-08-31  
Issue: #401  
Capability: CAP-084  
Parent: PR #400 exact-green head `df4ebd2d40eff1b36f567f0b09fee60bea26f50f`

## Context

The mobile account conversion flow allows guests to optionally protect their weigh history by verifying an email or phone number. However, the current client implementation:
1. Permitted silent no-op actions when requesting OTP with an empty identifier or verifying with an incomplete code.
2. Sent the user back to the beginning upon receiving `AUTH_OTP_INVALID` rather than keeping them on the verification step to correct their input.
3. Threw an unhandled `StateError` in Product Preview when an incorrect sample code was supplied instead of using the repository `ApiFailure` failure contract.
4. Rendered raw error code parameters when formatting failure strings.

## Decision

1. **Local Input Validation:**
   - The OTP request action is disabled whenever the identifier is empty or consists solely of whitespace.
   - The OTP verification action is disabled unless the entered code consists of exactly 6 numeric digits (`^[0-9]{6}$`).
   - Text inputs enforce numeric digits and maximum length constraints via platform input formatters.

2. **Error Recovery Boundaries:**
   - `AUTH_OTP_INVALID` is classified as a *retryable error*. The client remains on the `enterCode` step, displays a clear localized message, and allows the user to immediately correct the code without losing the active challenge.
   - Terminal errors (`AUTH_OTP_EXPIRED`, `AUTH_OTP_LOCKED`, `AUTH_RATE_LIMITED`, `AUTH_CHALLENGE_EXPIRED`, `AUTH_CHALLENGE_NOT_FOUND`, `AUTH_VERIFICATION_TOKEN_EXPIRED`, `AUTH_VERIFICATION_TOKEN_INVALID`, `AUTH_ACCOUNT_MERGE_FAILED`) transition the UI to an error state and clear the active challenge so the user can restart cleanly.
   - A dedicated "Change destination or request new code" action allows users on the code step to explicitly return to the identifier screen.

3. **Product Preview Boundary:**
   - `PreviewAccountRepository` throws `ApiFailure('AUTH_OTP_INVALID', 400)` for non-matching sample codes and `ApiFailure('AUTH_VERIFICATION_TOKEN_INVALID', 400)` for invalid tokens, eliminating unhandled `StateError` exceptions while preserving Preview/production isolation.

4. **Localization and Privacy:**
   - Bounded error messages are localized in Turkish and English for all known OTP failure scenarios.
   - Internal technical error codes are not displayed to the user.

5. **Invariants Preserved:**
   - Commit First, optional guest continuation, EMAIL/SMS channel selection, account merge and credential rotation semantics, backend API/OpenAPI contracts, and database models remain unchanged.

## Verification

The contract `docs/contracts/account-conversion-validation-recovery.v1.json`, controller unit tests, widget interaction tests, Preview repository tests, and localization tests must pass. Exact-head workflows `API CI`, `Mobile CI`, `MVP Beta Gates`, and `Global Readiness` are required before publication.

## Lifecycle

CAP-084 remains `IMPLEMENTED_PARTIAL`. This candidate does not update `docs/status/CURRENT.md` or promote capability lifecycle states.
