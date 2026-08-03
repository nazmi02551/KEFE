# Installable Phone Preview Hotfix Candidate — 2026-08-03

## Incident

A phone tester installed the production-entry compile artifact and reached a network error after the first onboarding decision. The decision remained on-device, but commit/reveal could not succeed because the APK was compiled against `https://beta-api.invalid/`.

## Root cause

The CI artifact boundary was ambiguous:

- the unconfigured production shell was uploaded as `kefe-mvp-beta-internal`;
- the actual offline-capable phone preview was uploaded separately as `kefe-internal-alpha-phone-preview`.

The preview entrypoint also inherited `SecureDecisionDraftStore`, allowing stale debug-install decision drafts to survive across artifact variants.

## Candidate correction

- Production `lib/main.dart` remains compiled for regression proof but its APK is no longer uploaded.
- `lib/main_preview.dart` is the only installable phone-test entrypoint.
- The installable workflow artifact is named `kefe-installable-phone-preview`.
- The APK filename is `KEFE-phone-preview-<exact-sha>.apk`.
- Preview composition uses `MemoryDecisionDraftStore` and cannot read production secure drafts.
- Production composition remains HTTP-backed and has no preview fallback.
- ADR-0090, executable contract and dedicated CI lock these boundaries.

## Evidence status

Candidate only until the exact hotfix head passes:

- Phone Artifact Boundary CI;
- MVP Beta Gates;
- Global Readiness, including phone acceptance and APK upload;
- general API/mobile regression workflows triggered by the stacked branch.

No production endpoint or deployed backend is claimed.
