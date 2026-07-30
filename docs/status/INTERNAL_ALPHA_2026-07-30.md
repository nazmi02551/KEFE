# KEFE Internal Alpha checkpoint — 2026-07-30

Status: **REPO_VERIFIED_INTERNAL_ALPHA / HUMAN_PHONE_USABILITY_PENDING**

This record pins the repository-owned Internal Alpha evidence produced by PR #97 (`feature/internal-alpha-hardening`), stacked on PR #95.

## Verified code candidate

`f7ab9b9d3db235bd9fdcc0c12950e5c181791018`

All required repository-owned workflows passed on that exact code SHA:

- API CI — run `30533434494` (#619) — SUCCESS
- Mobile CI — run `30533434478` (#435) — SUCCESS
- MVP Beta Gates — run `30533434476` (#123) — SUCCESS
- Global Readiness — run `30533434504` (#47) — SUCCESS

Later documentation/status-only commits do not redefine this verified code candidate. Any subsequent runtime, contract, workflow, migration, test or mobile-source change requires a fresh same-SHA verification before this checkpoint may move.

## Internal Alpha evidence closed

- production presentation copy boundary gate reports zero user-facing hardcoded-copy violations in its governed scope;
- direct per-screen TR/EN branching in governed production presentation scope is removed in favor of the localization boundary;
- System / Türkçe / English preference remains persistent and shared by production/Product Preview shells;
- System / Light / Dark preference remains persistent and shared by production/Product Preview shells;
- Flutter analyze passes;
- full Flutter regression suite passes;
- deterministic phone-acceptance suite passes for locale/theme persistence, Explore save→Activity→Case continuity, Weigh→Commit→Reveal, privacy/settings entry, and Share deep-link Blind First behavior;
- API 0.20 global discovery additive layer remains exact and 0.19 MVP baseline remains intact;
- PostgreSQL global migrations/seeds plus existing MVP regressions pass;
- Commit First / Blind First, immutable CaseVersion, case-agnostic runtime and preview-production isolation remain unchanged;
- My KEFE remains observed/descriptive history only; Signal and Impact remain outside this slice.

## Internal phone artifact

Global Readiness artifact:

- name: `kefe-internal-alpha-phone-preview`
- artifact ID: `8755762971`
- artifact archive digest: `sha256:c3bd8c0cc870494884a556dcb26a3c7be5a4bb79575474c25fab0d2263c4b475`
- artifact head SHA: `f7ab9b9d3db235bd9fdcc0c12950e5c181791018`

Extracted APK verification:

- file: `KEFE-Internal-Alpha-f7ab9b9d.apk`
- SHA-256: `d82787eda33c3f886a1e0c23997b8e51944956660d0878cd326e81f902257f07`
- `beta-api.invalid`: not present in raw or unpacked APK inspection.

The APK is an isolated Product Preview/internal phone candidate. It is not a production/store release and Product Preview fixtures are not production fallback.

## Evidence intentionally still pending

The following remain external/human gates and are not converted into PASS by repository CI:

- human phone usability on the exact candidate APK;
- real production OTP provider configuration and deliverability;
- editorial CQB acceptance of launch content;
- current Apple/Google store compliance review;
- deployed production SLO/load/observability evidence;
- operator-validated production feature-switch/rollback controls.

Until those are evidenced, do not call this `BETA_GATE_PASSED`, public release-ready, or store-ready.

## Next recommended phase

Run a structured human phone usability pass against this exact APK before expanding product scope. Capture friction, layout/accessibility, language/theme behavior and the Golden Path on real hardware. Product changes discovered by that pass should be implemented on a new stacked slice and must receive a fresh exact-head verification.
