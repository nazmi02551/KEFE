# Premium First-Use Journey Slice 16 — Verified Checkpoint

Date: 2026-07-31

## Status

**REPO-VERIFIED INTERNAL PHONE CHECKPOINT**

This status record pins the exact runtime candidate below. Any later documentation-only commit on the stacked branch does not redefine the verified runtime SHA.

## Verified runtime

- Runtime SHA: `86b75bb621b866770371f34500a2fc7148bac484`
- Branch: `feature/premium-first-use-slice16`
- Draft PR: #128
- Stack base: PR #126 / `feature/premium-social-participation-slice15`
- Issue: #127
- ADR: `docs/adr/0054-premium-first-use-journey.md`
- Executable contract: `docs/contracts/premium-first-use-slice16.v1.json`

## Scope proved at this checkpoint

- The existing two-page first-use onboarding now uses visibly premium, theme-adaptive KEFE semantic surfaces and the established balance visual vocabulary.
- Onboarding loading presentation is deterministic/non-continuous; no continuous onboarding spinner remains.
- Page progress and page transition duration use the existing Reduce Motion-aware `KefeMotion.resolve` boundary.
- Existing localized onboarding wording, exactly two promise pages, stable interaction keys and demo Case handoff remain unchanged.
- The first real Case still opens only after the two current promises and still uses the existing `firstUse=1` route behavior.
- Onboarding completion remains persisted through the existing Decision flow after the first Reveal transition.
- The existing first-Reveal completion surface now uses a premium KEFE semantic surface while preserving `continue-as-guest` and `/explore` continuation.
- TR/EN light/dark regression coverage and Slice 16 contract/source checks were added.
- Existing onboarding flow tests continue to prove fresh-user, first-Reveal completion and completed-user bypass behavior.

## Exact-head CI evidence

All required workflows completed successfully on the same runtime SHA `86b75bb621b866770371f34500a2fc7148bac484`:

- API CI #810 — run `30638495387` — SUCCESS
- Mobile CI #612 — run `30638495494` — SUCCESS
- MVP Beta Gates #314 — run `30638495458` — SUCCESS
- Global Readiness #224 — run `30638495376` — SUCCESS

Observed gates include canonical Dart formatting, Flutter analyzer, full mobile regressions, accessibility/locale/theme regression suite, production-copy boundary, phone acceptance, API contracts/generic-runtime continuity, PostgreSQL continuity and Global API/PostgreSQL gates.

## Phone artifact evidence

Global Readiness run `30638495376` produced:

- Artifact: `kefe-internal-alpha-phone-preview`
- Artifact ID: `8796551245`
- Artifact archive digest: `sha256:cd557299f2c69ce87161974bd50a27325584732e469ada18e5b9c78e094961da`
- APK payload: `app-debug.apk`
- APK SHA-256: `addacc15e10ca271b3510ac1ee6ec26596042adcaf88ddc931146a38dc364689`
- `beta-api.invalid` raw APK scan: ABSENT
- `beta-api.invalid` unpacked APK scan: ABSENT

## Rejected candidate

- `d1e954f33061de5ad0e06edfb2f270021b1b4da6` — rejected because MVP Beta Gates found canonical Dart formatting drift in the new Slice 16 test source. The CI-normalized formatter output was applied before the accepted runtime.

The verified runtime is only `86b75bb621b866770371f34500a2fc7148bac484`.

## Boundaries and non-claims

This checkpoint does **not** authorize or prove:

- a new onboarding step, new onboarding product claim or altered onboarding copy;
- a different demo Case or Case-selection policy;
- backend/API/schema/controller/route architecture changes;
- pre-Commit collective/result exposure;
- Signal/Impact expansion;
- personality, ideology, psychometric, bias or causal inference;
- production OTP/provider readiness;
- editorial CQB completion;
- store compliance or production deployment readiness;
- production SLO/operator rollback evidence;
- human real-device usability validation.

Commit First, Blind First, immutable CaseVersion, case-agnostic generic runtime, preview/production isolation and My KEFE observed/descriptive-only boundaries remain unchanged.

## Governance

PR #128 remains draft and stacked. Merge order must be checked before promotion. This repo-verified checkpoint may be mirrored into KEFE/WORKING documentation, but it does not supersede or silently rewrite the accepted CURRENT documentation baseline.
