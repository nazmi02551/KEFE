# ADR-0145 — Account conversion validation and recovery

Status: CANDIDATE  
Date: 2026-08-31  
Issue: #401  
Capabilities: CAP-084, CAP-095  
Parent: PR #400 exact-green head `df4ebd2d40eff1b36f567f0b09fee60bea26f50f`

## Context

The optional account-protection flow already requests an email/SMS OTP,
verifies it, merges the guest identity and atomically replaces the credential
bundle. Its mobile recovery behavior is incomplete:

- an empty identifier or incomplete code produces a silent no-op;
- a retryable invalid OTP hides the code step and sends the user back to the
  identifier step;
- terminal challenge failures are displayed as raw internal codes;
- Product Preview throws an uncaught adapter error for an incorrect sample
  code.

The API already distinguishes retryable `AUTH_OTP_INVALID` from expired, used,
missing or locked challenges. Mobile can honor that existing boundary without
changing OTP delivery, verification or merge semantics.

## Decision

1. The Send code action is disabled until the identifier contains a non-empty
   value after trimming. Server-side normalization and validation remain
   authoritative.
2. The Convert action is disabled until the local code is exactly six decimal
   digits. The field rejects non-digit input; server verification remains
   authoritative.
3. `AUTH_OTP_INVALID` is recoverable on the current challenge. Mobile keeps the
   code step and allows the user to correct and submit another code.
4. `AUTH_OTP_EXPIRED`, `AUTH_OTP_CHALLENGE_USED`,
   `AUTH_OTP_CHALLENGE_NOT_FOUND`, `AUTH_OTP_ATTEMPTS_EXCEEDED`,
   `AUTH_VERIFICATION_INVALID` and `AUTH_MERGE_REPLAY_MISMATCH` cannot safely
   reuse the current challenge. Mobile clears it and returns to the
   identifier/new-code path while preserving the entered destination.
5. A transport failure during verification or merge also requires a new code,
   because the client cannot know whether the previous verification token was
   consumed after a lost response.
6. Turkish and English present bounded, actionable messages for known OTP and
   merge states. Unknown internal error codes are not rendered to the user.
7. Editing a retryable code clears the stale error while keeping the challenge.
8. Product Preview maps an incorrect sample code to the same
   `AUTH_OTP_INVALID` repository failure contract. It does not claim real OTP
   delivery or production provider behavior.
9. Account conversion remains optional; Continue as guest stays available.
10. Channels `EMAIL`/`SMS`, account merge, credential rotation/replacement,
    guest history preservation, API, OpenAPI, persistence and database
    semantics remain unchanged.

## Recovery table

| Failure | Mobile step | Current challenge |
| --- | --- | --- |
| `AUTH_OTP_INVALID` | code entry | preserved |
| expired/used/not found/attempts exceeded | identifier/new code | cleared |
| invalid verification/merge mismatch | identifier/new code | cleared |
| verification or merge transport failure | identifier/new code | cleared |
| request/delivery failure | identifier/new code | absent |

## Accessibility and privacy

- Disabled states are visible through standard Material button semantics.
- The OTP field retains one-time-code autofill and gains digits-only input.
- Error text is localized and does not expose identifiers, challenge IDs,
  verification tokens, actor IDs or raw internal codes.
- Compact phones, enlarged text, light/dark themes and screen readers remain
  supported by the existing scrollable surface.

## Verification

The executable contract
`docs/contracts/account-conversion-validation-recovery.v1.json`, controller
tests, Turkish/English widget coverage, Preview recovery test and full mobile
regression suite must pass. API CI, Mobile CI, MVP Beta Gates and Global
Readiness must all complete on the same exact PR head before this candidate is
called PASS.

## Lifecycle

CAP-084 remains `IMPLEMENTED_PARTIAL`; CAP-095 remains `ONGOING_MANDATORY`.
This candidate does not update `docs/status/CURRENT.md`. Human review,
production provider operation and capability governance remain separate gates.
