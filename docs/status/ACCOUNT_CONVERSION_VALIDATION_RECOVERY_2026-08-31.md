# Account conversion validation and recovery — 2026-08-31

Status: IMPLEMENTATION CANDIDATE / EXACT-HEAD CI PENDING / NO CAPABILITY PROMOTION

Issue: #401  
Capability: CAP-084 (`IMPLEMENTED_PARTIAL`)  
Stack base: PR #400 exact-green head `df4ebd2d40eff1b36f567f0b09fee60bea26f50f`

ADR: ADR-0145  
Contract: `docs/contracts/account-conversion-validation-recovery.v1.json`

## User-visible outcome

The account conversion interface now enforces strict local input validation before triggering network actions. Request and verify actions remain disabled until their minimum requirements (non-empty identifier, exactly 6 numeric OTP digits) are met.

When an incorrect code is entered, the interface now keeps the user on the verification code step, displays a clear localized error, and allows immediate correction without forcing the user to restart from the beginning. Terminal conditions (expired codes, rate limits, expired verification sessions) cleanly guide the user back to request a fresh code.

Product Preview sample verification now fails gracefully with standard repository failure semantics instead of throwing uncaught exceptions.

## Preview and privacy boundary

Product Preview uses mock sample code `123456` and fails closed on incorrect input without making live network requests. All OTP error scenarios are localized in Turkish and English without leaking internal technical codes or raw identifiers.

## Evidence boundary

- Machine-readable contract: `account-conversion-validation-recovery.v1.json` (PASS);
- ADR: `ADR-0145` (PASS);
- Account controller tests covering empty input rejection, retryable code retention, and terminal challenge resets: PASS;
- Preview repository `ApiFailure` failure contract tests: PASS;
- Turkish and English localization catalog tests: PASS.

Required exact-head CI workflows: `API CI`, `Mobile CI`, `MVP Beta Gates`, `Global Readiness`.

## Lifecycle

CAP-084 remains `IMPLEMENTED_PARTIAL`.
