# KEFE Perspective Landscape Convergence — Slice 20

Date: 2026-07-31  
Status: REPO_VERIFIED / HUMAN_VISUAL_USABILITY_PENDING  
Issue: #142  
PR: #143  
ADR: ADR-0058  
Executable contract: `docs/contracts/perspective-landscape-slice20.v1.json`

## Verified runtime

Exact runtime SHA:
`d33596da0c7fb6d8a6a43b620ce11c5bf38c850f`

Any later documentation-only commit on PR #143 must not redefine this verified runtime.

## Exact-head CI evidence

All four required workflows completed successfully on the exact same runtime SHA:

- API CI #880 — run `30664464724` — SUCCESS
- Mobile CI #676 — run `30664464705` — SUCCESS
- MVP Beta Gates #384 — run `30664464717` — SUCCESS
- Global Readiness #288 — run `30664464689` — SUCCESS

Verified gates include canonical Dart formatting, analyzer, full Flutter regressions, Perspective consumption/retry behavior, production-copy boundary, phone acceptance, API/generic-runtime contracts, PostgreSQL MVP/global regressions and Android candidate builds.

## What Slice 20 implemented

### Qualitative Perspective Landscape
The existing post-Commit Perspective loaded surface now includes a reusable Flutter-native qualitative landscape driven only by recognized `PerspectiveCard.slot` presence:
- `NEAR`
- `OPPOSING`
- `BRIDGE`
- `ALTERNATIVE_CONTEXT`

The renderer uses deterministic topographic contours, mesh, ambient depth and fixed slot beacons. It is presentation grammar, not a statistical or ideological coordinate system.

The existing Perspective cards remain the complete semantic/text representation and remain in API order. Existing methodology, curated-fallback and cluster-pending disclosure remain visible.

### Quantitative truthfulness preserved
The current Perspective payload has no measured user coordinate, population-density coordinate, user/community percentage, ideological/value/psychometric position or measured user-community distance.

Therefore Slice 20 explicitly does **not** render:
- `Sen %...` or `Toplum %...`;
- a measured user marker;
- population-density peaks;
- ideological/value/psychometric coordinates;
- correctness, popularity, consensus-authority or measured-distance geometry.

A future quantitative Perspective Landscape requires a separate methodology/data ADR and executable contract.

### Post-Commit boundary preserved
The landscape is reachable only inside the existing Perspective flow after successful Commit and Reveal/Perspective load.

Executable regressions prove:
- no Perspective landscape before Commit;
- Reveal continues into Perspective and then the landscape;
- all existing Perspective cards remain present;
- Perspective retry does not replay answer, private reason, Commit or Reveal;
- the landscape appears after successful Perspective retry.

### Generic runtime preserved
The landscape is driven by slot enum presence only. No Case ID/title/domain branch was introduced. No local reranking or Perspective repository/domain/API/schema change was introduced.

### Accessibility / performance
- dark and light theme coverage;
- compact phone height/width coverage;
- 1.6× enlarged-text legend coverage;
- decorative terrain is excluded from semantics;
- existing cards remain semantic content truth;
- no text is painted into the terrain canvas;
- `RepaintBoundary` isolates custom painting;
- no continuous idle animation, WebView, Three.js or mandatory live 3D.

## Rejected candidate

No PASS claim attaches to:
- `39994971155d926ca7611ac069b76ffc2dac05dd` — MVP mobile canonical Dart format gate failed for the new Landscape source/test. API and PostgreSQL evidence on that head did not make the runtime acceptable. Canonical formatter output was applied exactly, then all four workflows were rerun on the final runtime SHA.

## Phone artifact evidence

From Global Readiness #288 / run `30664464689`:

- artifact name: `kefe-internal-alpha-phone-preview`
- artifact ID: `8806520644`
- archive digest: `sha256:ed9d163c74878ee098aceed09c962d23afdf23c7b05a03c88d7db2c0367724de`
- runtime SHA: `d33596da0c7fb6d8a6a43b620ce11c5bf38c850f`
- payload: `app-debug.apk`
- APK size: `160552254` bytes
- APK SHA-256: `701220868a1bc9fe071e67cb8dcf7963de4c94fda32498037d755f98a59cf378`
- `beta-api.invalid`: NOT FOUND in raw APK
- `beta-api.invalid`: NOT FOUND in unpacked APK

This artifact is an isolated internal Product Preview candidate, not a production/public-beta/store release.

## Not claimed

Slice 20 does not claim:
- measured user/community position;
- population density or percentile;
- ideology/value/personality/psychometric/bias inference;
- objective correctness or recommendation;
- Signal/Impact readiness;
- human visual approval or human usability PASS;
- production OTP/provider/store/SLO/rollback readiness.

## Next visual slice

With Signature Balance, Atlas World and qualitative Perspective Landscape repo-verified, the next planned high-fidelity adoption is **Spatial CALL Convergence**. Its contract must first audit the actual current CALL question/media schema and may render only data already present in the immutable CaseVersion/media model; it must not invent camera geometry, offside lines, VAR evidence or adjudication metadata that the domain does not provide.
