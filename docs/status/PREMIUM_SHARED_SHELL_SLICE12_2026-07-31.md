# KEFE Premium Shared Navigation Shell Slice 12 — Verified Checkpoint

- Date: 2026-07-31
- Issue: #119
- PR: #120 (`feature/premium-shell-slice12`), stacked on PR #118
- ADR: ADR-0050
- Executable contract: `docs/contracts/premium-shell-slice12.v1.json`
- Pinned verified runtime / artifact head SHA: `b4f1e5405e022132618c5cc142172c0290b5c3c0`

## Repository-owned verification

All required repo-owned workflows succeeded on the same pinned SHA `b4f1e5405e022132618c5cc142172c0290b5c3c0`:

- API CI `30626140285` (#776) — SUCCESS
- Mobile CI `30626140252` (#580) — SUCCESS
- MVP Beta Gates `30626140387` (#280) — SUCCESS
- Global Readiness `30626140194` (#192) — SUCCESS

The exact-head gates include canonical Dart formatting, analyzer, full Flutter regressions, Slice 12 TR/EN light/dark shell coverage, canonical navigation continuity, production copy boundary, automated phone acceptance, API contracts/tests, PostgreSQL migrations/seeding/integration, generic-runtime gates and global-readiness API/PostgreSQL checks.

An earlier candidate `6706611e30ddc81c380aad35ffc2afd3ee451360` was not accepted: MVP mobile reported Dart format drift and Mobile CI exposed an `OutsideTestException` in the new Slice 12 path assertion. Those issues were corrected before the pinned candidate. No PASS claim attaches to the earlier candidate.

## Closed in Slice 12

- The canonical four-tab shell now uses shared theme-adaptive KEFE semantic surface, border and shadow roles instead of a direct `KefeColorTokens.borderDark` dependency.
- The canonical tab model is unchanged: `/explore`, `/weigh`, `/activity`, `/my-kefe`, exactly four destinations, with the existing `primary-navigation` key and selected-index routing semantics preserved.
- Production and Product Preview settings access now share a restrained KEFE shell action treatment while preserving `open-settings` and `open-preview-settings` on the interactive controls.
- Product Preview Radar and Atlas actions use the same shell action vocabulary but remain secondary destinations; they were not promoted into the primary tab model.
- Product Preview build identity remains truthful through `PreviewBuildInfo.label` while moving from fixed dark-only `surfaceDark` / `textMutedDark` styling to semantic theme-adaptive roles.
- Radar/Atlas secondary route chrome now uses semantic KEFE surface/foreground/border roles while preserving existing titles and back behavior.
- New Slice 12 tests cover the executable contract, canonical paths, four destinations, TR/EN rendering, light/dark semantic shell roles, action sizing/styling, route-selection continuity and direct-dark-token source boundaries.
- No backend, read-model, CaseVersion, decision-flow, Signal/Impact or product-mode behavior changed.
- Commit First, Blind First, immutable CaseVersion, case-agnostic generic runtime, preview/production isolation and My KEFE descriptive-only/no-inference boundaries remain unchanged.

## Internal phone artifact

- Artifact: `kefe-internal-alpha-phone-preview`
- Artifact ID: `8791544339`
- Artifact archive digest: `sha256:2d02ac1fb9ed1e907fd24019979f1dec472b7960fbef72a5338e59efbfd05f68`
- Artifact head: `b4f1e5405e022132618c5cc142172c0290b5c3c0`
- Payload: `app-debug.apk`
- APK SHA-256: `aeb8ffd15e578fbfffecdde05889766a537b1de137849c6285016728434d4217`
- `beta-api.invalid`: absent from raw APK scan.

This artifact is internal Product Preview / automated phone-review evidence only. It is not production/store release evidence and does not establish a human usability pass.

## Still open after Slice 12

- human real-device screenshot/usability review of this exact checkpoint where required;
- premium convergence of settings/privacy/account/share/community surfaces selected by a fresh contract-first audit;
- empty/loading/error/skeleton-state taxonomy and remaining shared typography/spacing consistency where repo audit proves debt;
- stacked-PR promotion/mainline verification in dependency order;
- production OTP/provider evidence, editorial CQB, current store compliance/signing, deployed production SLO/load/observability and operator-validated production switch/rollback.

No external gate is marked PASS by this checkpoint.

## Documentation state

This checkpoint is branch-stack/repository evidence. It does not promote or overwrite the Google Drive canonical CURRENT documentation baseline. WORKING documentation may reference this exact verified SHA; canonical CURRENT promotion remains a separate stack/release-baseline decision.
