# KEFE Product Completion + Visual Roadmap — 2026-07-31

Status: WORKING / stacked planning record
Top verified runtime before Slice 17 runtime work: `68b390584901dc706059485afb6f29d7f073defc` (Slice 16 corrected)
Top planning branch: `feature/high-fidelity-visual-foundation-slice17`
Canonical tracker: #129

This record summarizes what is already repo-verified on the active stacked line and what remains before a four-dörtlük consumer product can be claimed. It does not promote the stack to main and does not supersede Drive CURRENT v3.4.

## 1. What is already built on the active stack

### Product/runtime foundation
- Case-agnostic composable runtime and immutable CaseVersion execution.
- Commit First / Blind First boundaries and pre-/post-Commit separation.
- Explore, Case, Context, typed Weigh, private Reason, Commit, Reveal and Perspective journey.
- Activity/Saved Cases continuity and descriptive My KEFE history.
- Case-only sharing under Blind First.
- Post-Commit Consensus and Community Reasons within their existing bounded contracts.
- Settings, privacy controls and optional account-conversion presentation while real production OTP remains external/pending.
- Product Preview/production isolation and deterministic phone-test artifacts.

### Platform/readiness foundation
- FastAPI/PostgreSQL backend, versioned contracts, migrations and generic runtime gates.
- Localization resource architecture: TR/EN enabled, deterministic English fallback for unsupported resource lookup, no third-locale support claim.
- System/Light/Dark theme preferences and semantic KEFE visual tokens/surfaces.
- Shared four-tab mobile shell: Explore / Weigh / Activity / My KEFE.
- Accessibility/Reduce Motion foundations, production copy boundary and phone-acceptance automation.
- Exact-head CI discipline across API CI, Mobile CI, MVP Beta Gates and Global Readiness.

### Premium convergence through Slice 16
1. Decision Journey foundation.
2. Reveal + KEFE Gap.
3. Perspective/counter-view.
4. Radar preview.
5. Atlas preview.
6–10. Localization foundation and convergence.
11. Activity + My KEFE.
12. Shared navigation shell.
13. Settings + Privacy + Account.
14. Blind First sharing.
15. Consensus + Community Reasons.
16. First-use/onboarding + first-Reveal completion, including corrected phone-preview reachability.

## 2. What the concept references mean

The premium concept screenshots supplied during product development are target art direction. They express desired visual quality and interaction language such as:
- signature physical-looking KEFE balance hero;
- rich Atlas/world visual;
- Perspective landscape/terrain visual language;
- Spatial CALL field/camera-angle visual language.

They are not pixel-exact specifications, current runtime evidence, new methodology or permission to introduce screen-specific runtime branches.

The current app is intentionally an intermediate premium foundation, not yet that final art-direction fidelity.

## 3. Foundation-first next sequence

### Slice 17 — High-Fidelity Visual Composition Foundation
Before building screen-specific photorealistic/rich scenes, establish shared infrastructure for:
- semantic visual/scene slots;
- provider-neutral asset/rendition descriptors;
- asset identity/hash and provenance;
- aspect/focal crop/safe-area/theme suitability;
- PRE_COMMIT_SAFE / POST_COMMIT_ONLY exposure;
- deterministic loading/empty/error/fallback;
- decorative vs semantic accessibility;
- optimized static/pre-rendered assets + lightweight Flutter overlays;
- low-end Android decode/cache/memory/performance budgets;
- Reduce Motion;
- theme/locale/text-scale/golden visual regression.

No WebView/Three.js or mandatory live 3D engine is planned for this foundation.

### After foundation verification
Initial high-fidelity adoption order:
1. Weigh / signature Balance hero.
2. Atlas world/globe hero.
3. Perspective Landscape.
4. Spatial CALL scene.
5. Remaining primary-screen loading/empty/error/skeleton, typography and spacing convergence.

Each remains a separate contract-first vertical slice. The order can change only from a fresh audit or accepted product decision, not ad hoc implementation convenience.

## 4. What still blocks a final/public product claim

### Repo/product work still remaining
- High-fidelity visual composition foundation and the screen convergence above.
- Remaining systematic state/component/typography/spacing convergence found by fresh audits.
- Mainline promotion of the long draft stack in dependency order, with resulting mainline verification.
- Any still-deferred capabilities explicitly selected from Product Bible/Roadmap Capability Register through their own contracts.

### External/human evidence still pending
- Human phone usability/visual review on accepted exact candidate builds.
- Real production OTP/provider configuration and deliverability.
- Editorial CQB acceptance of launch content.
- Current Apple/Google store compliance/signing/review evidence.
- Deployed production SLO/load/observability evidence.
- Operator-validated production switch/rollback controls.

CI cannot convert these external items to PASS.

## 5. Documentation propagation

Do not create a new permanent official logical document for this visual strategy.

Working decisions live in Git ADR/contract/status plus the Drive WORKING checkpoint. At the next declared documentation publication milestone, synchronize accepted changes into:
- Design System: scene/hero taxonomy, visual asset/rendition/state/accessibility/performance/golden rules;
- Engineering Blueprint: asset resolution/adapters/cache/performance/test architecture;
- Product Bible: target art-direction adoption pattern and screen sequence;
- MVP Delivery Plan only if schedule/gates materially change.

Master Product Document changes only if product semantics/constitutional principles change. The current visual foundation decision does not require that.

## 6. Continuation rule

A future ChatGPT/Codex session must not depend on chat history. The phrase **“KEFE’yi geliştirmeye devam et”** means:
1. Read `docs/status/CURRENT.md` from `main`.
2. Inspect current open PR stack, top PR head, recent merges and CI before acting.
3. Resolve the top accepted/verified working checkpoint; distinguish verified runtime SHA from later docs-only head.
4. Read relevant ADR/executable contract and Drive CURRENT/WORKING authority where needed.
5. Continue the next unresolved item in dependency order; do not restart product analysis.
6. Ask the user only when a material product/architecture decision is genuinely unresolved; do not ask for already-known repo/history context.
7. Contract first for boundary changes; runtime second; tests/CI/evidence with implementation.
8. Never merge out of stack order or treat preview as production fallback.
9. Never claim PASS without the required evidence.

This rule should be reflected in the canonical `docs/status/CURRENT.md` handoff on main and kept current after meaningful milestones.
