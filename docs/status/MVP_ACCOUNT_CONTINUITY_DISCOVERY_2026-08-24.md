# MVP Account Continuity Discovery — 2026-08-24

Status: DRAFT CANDIDATE / NO CAPABILITY PROMOTION

Issue: #369

Capabilities: CAP-084 (primary), CAP-095 (supporting)

Base: PR #368 / `feature/mvp-horizontal-discovery-breadth` exact-green head `c1d8049d1b6c75d55a99175031a3f58bed10e519`.

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

## Stack convergence recovery

The previous PR #370 head `738aa0ee2eaeba4a77d1a24dc92df5591fdbcbbd`
remains historical evidence. It diverged from the old PR #368 base
`25811bfd50d2fb961e5ad2fe67e8e1f1ea6e4fee` and accumulated copies of CI,
formatting and localization fixes that are now already present and exact-green in
the parent.

The candidate was rebuilt on the exact-green parent with only this slice's five
owned files: two localization contracts, Settings presentation, focused
regression coverage and this checkpoint. The inherited privacy bearer-cache
checker correction remains supplied by the parent. No duplicated runtime or CI
fix is replayed in this child.

## Verification boundary

Focused repository regression coverage checks:

- Settings contains the explicit account-continuity entry and `/account` navigation;
- opening Settings has no direct AccountController/Repository dependency;
- Privacy remains separately reachable;
- EN/TR account-continuity copy exists and preserves guest optionality;
- production and Product Preview still reuse the same governed account route;
- Account Conversion still exposes `Continue as guest`.

No post-convergence exact-head GitHub Actions PASS is claimed yet. Source
comparison and focused regression intent are repository evidence only, not
executed Flutter/CI evidence or human usability approval.

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
