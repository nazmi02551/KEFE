# MVP Account Continuity Discovery — 2026-08-24

Status: DRAFT CANDIDATE / NO CAPABILITY PROMOTION

Issue: #369

Capabilities: CAP-084 (primary), CAP-095 (supporting)

Base: PR #368 / `feature/mvp-horizontal-discovery-breadth` exact head `25811bfd50d2fb961e5ad2fe67e8e1f1ea6e4fee`.

## Why this slice exists

The horizontal-first MVP breadth strategy requires account/privacy surfaces to be demonstrable at a safe candidate level before another long hardening sequence. Privacy is already reachable from Settings, and both production and Product Preview already register the governed `/account` route, but the account-continuity flow had no normal user-visible entry point.

This left a real product surface implemented but effectively hidden.

## Delivered boundary

Settings now exposes one explicit localized **Account and continuity / Hesap ve devamlılık** entry.

The entry:

- routes only to the existing `/account` flow;
- performs no identity/account request on Settings mount;
- makes account linking optional;
- explicitly preserves guest use in EN/TR copy;
- makes no cross-device/cloud-sync promise;
- keeps Privacy and Data as a separate explicit control;
- reuses the existing production and Product Preview account route/composition;
- preserves the existing `Continue as guest` exit from Account Conversion.

## Architecture and security boundary

No account, identity, credential, session, privacy, API, OpenAPI, schema or migration behavior changes in this slice.

The existing AccountController/Repository remains the only account-conversion runtime authority. Settings does not inspect actor kind, decode credentials, prefetch identity state, auto-request OTP or auto-convert a guest.

PR #367 session-renewal hardening remains a separate deferred-depth line under the horizontal-first strategy.

## Verification boundary

Focused repository regression coverage checks:

- Settings contains the explicit account-continuity entry and `/account` navigation;
- opening Settings has no direct AccountController/Repository dependency;
- Privacy remains separately reachable;
- EN/TR account-continuity copy exists and preserves guest optionality;
- production and Product Preview still reuse the same governed account route;
- Account Conversion still exposes `Continue as guest`.

The first exact-head Mobile CI run exposed a pre-existing checker false positive: `validate_mobile_privacy_actor_bound_deletion.py` scanned the whole decision repository file and rejected the legitimate in-memory CredentialStore field `String? _token;` as if it were a parallel `HttpDecisionRepository` bearer cache. The checker is now scoped to the `HttpDecisionRepository` class body, preserving the contract prohibition while allowing the credential-store implementation.

That checker correction changes no runtime or privacy semantics. New exact-head workflow evidence is required after the correction; no PASS is inferred from the failed predecessor run.

Static connector readback and source-regression intent are repository evidence only, not executed Flutter/CI evidence or human usability approval.

## Non-claims

This slice does not claim:

- session-renewal completion;
- account-state detection in Settings;
- cross-device synchronization;
- production OTP deliverability;
- identity production readiness;
- CAP-084 or CAP-095 lifecycle promotion;
- deployed Connected Alpha proof;
- store/release readiness.
