# KEFE Product Completion + Visual Roadmap — 2026-07-31

Status: WORKING / stacked planning record
Top verified runtime before Slice 17 runtime work: `68b390584901dc706059485afb6f29d7f073defc` (Slice 16 corrected)
Top planning branch: `feature/high-fidelity-visual-foundation-slice17`
Canonical visual-foundation tracker: #129

This record summarizes what is already repo-verified on the active stacked line and what remains before a four-dörtlük consumer product can be claimed. It does not promote the stack to main and does not supersede Drive CURRENT v3.4.

Important scope distinction: finishing the current premium visual program does **not** mean the whole KEFE product roadmap is finished. The core launch/MVP experience, architecture-locked implementation debt and accepted-later Product Bible capability horizon are separate layers.

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

## 3. Foundation-first visual sequence

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

## 4. Non-visual architecture and product work still exists

### 4.1 Architecture locked, implementation still pending or incomplete
The repository already contains contracts whose semantics are accepted but whose full runtime is not yet implemented. These are not visual polish:

- **Provider-neutral ingestion orchestration**: durable ingestion runs/stages, proposal/review/materialization, bounded retry and provider-neutral processors are architecture-locked; the contract still marks the first implementation slice pending. External source/AI provider calls, Admin queue UI and Candidate Case → authoring-draft projection remain separately deferred.
- **Editorial projection**: accepted Candidate Cases / Decision Problems / Question Drafts still require an explicit projection contract into the existing Content Authoring lifecycle; automatic publication remains forbidden.
- **WE → SIGNAL → IMPACT**: the methodology-qualified Signal and verified Impact lifecycle is architecture-locked, but its contract is explicitly implementation-pending. Collective Result/Consensus must not be treated as Signal by shortcut.
- **Operational/Admin maturity**: secured Admin foundations exist, but future editorial/review queue and full operational studio capabilities must be implemented only through explicit contracts.
- **Production provider/runtime maturity**: real auth/OTP, notification, storage/search/billing/provider implementations stay behind ports/adapters and require real environment evidence before production claims.

These items must be prioritized independently from visual work according to MVP/release need; visual completion must never be used to declare them complete.

### 4.2 Accepted-later Product Bible capability horizon
The canonical Roadmap Capability Register intentionally preserves future product families. They are not automatically launch blockers and must not be speculative-implemented, but the architecture must remain able to accommodate them. Current registered families include:

- **Trust / real-world**: KEFE Today, Evidence Builder and deeper source/claim workflows.
- **Global / intelligence**: fuller Case Atlas, later Values Atlas after methodology validation, Context Lens, Chronicle, Temporal Retest and Outcome Triangle.
- **Social without follower-network dependence**: KEFE Circle / Birlikte Tart, later Rooms and UGC Personal Dilemmas under privacy/moderation controls.
- **New interaction formats**: KEFE Live, full DECIDE and RETRO experiences; current base-format architecture must allow these without named-Case runtime branches.
- **Learning / reasoning tools**: Perspective Coach, AI Devil’s Advocate, Debate/Sparring and Education/Classroom, with AI identity and safety boundaries explicit.
- **Alternative consumption/retention**: Observe / Sadece Oku, Wrapped and Decision Fatigue quality controls.
- **Research / platform**: KEFE Research, aggregate Insights, Pulse and Aggregate API; user-level private history is not exposed through aggregate products.
- **Long-horizon methodology/governance**: validated Values/profile work, global indices and possible Standards Council only after their evidence/governance prerequisites.

A future product decision chooses which of these become actual delivery slices and when. Their presence in the register means “preserved product direction”, not “build all before launch”.

### 4.3 Launch/MVP versus long-term KEFE
For the first strong public consumer release, the primary product remains the fast independent-decision loop plus bounded post-Commit value: Explore → Case/Context → Weigh → Commit → Reveal → Perspective, with Activity/My KEFE, safe sharing, account/privacy and approved participation surfaces.

The public-release checklist must separately decide which architecture-pending non-visual items are launch-blocking. Post-MVP families above do not become launch blockers merely because they are canonical roadmap items.

## 5. APK / Product Preview fidelity gate

A phone APK is faithful only to its **exact verified runtime SHA**, not to every later branch/document automatically.

For every future phone candidate, record and test:
1. exact runtime SHA, CI runs, artifact ID/digest and APK hash;
2. production route/surface inventory at that SHA;
3. Product Preview route/surface inventory at that SHA;
4. every implemented user-facing surface classified as:
   - production-and-preview reachable,
   - production-only with reason,
   - preview-only with reason,
   - conditional/feature-gated with an explicit review path or explicit exclusion;
5. provider substitutions/fixtures used by Product Preview;
6. any behavior intentionally impossible to prove in preview (real OTP/provider delivery, production network/SLO, store behavior, etc.);
7. no already-implemented intended review surface may silently disappear from the candidate artifact.

The Product Preview may add safe review access (for example first-use replay, Radar/Atlas previews) but may not replace production semantics or use preview fixtures as production fallback.

A candidate must not be described as “the current app on the phone” without passing this reachability/parity inventory against its exact runtime SHA.

## 6. What still blocks a final/public product claim

### Repo/product work still remaining
- Implement and repo-verify Slice 17 visual composition foundation and selected high-fidelity screen slices.
- Execute the architecture-pending non-visual slices that are accepted as required for the target release.
- Complete APK/Product Preview reachability/parity inventory for meaningful phone checkpoints.
- Continue fresh audits for remaining component/state/typography/spacing/accessibility/performance debt.
- Promote the draft stack to main in dependency order and verify the resulting mainline state.
- Select accepted-later Product Bible/Roadmap Capability Register items only through explicit product decisions/contracts; do not assume every deferred capability is launch-blocking.

### External/human evidence still pending
- Human phone usability/visual review on accepted exact candidate builds.
- Real production OTP/provider configuration and deliverability.
- Editorial CQB acceptance of launch content.
- Current Apple/Google store compliance/signing/review evidence.
- Deployed production SLO/load/observability evidence.
- Operator-validated production switch/rollback controls.

CI cannot convert these external items to PASS.

## 7. Documentation propagation

Do not create a new permanent official logical document for this visual strategy or duplicate the Product Bible capability register.

Working decisions live in Git ADR/contract/status plus the Drive WORKING checkpoint. At the next declared documentation publication milestone, synchronize accepted changes into:
- Design System: scene/hero taxonomy, visual asset/rendition/state/accessibility/performance/golden rules;
- Engineering Blueprint: asset resolution/adapters/cache/performance/test architecture and phone-candidate parity gate if accepted;
- Product Bible: target art-direction adoption pattern and screen sequence; retain the existing capability register as the long-term product horizon;
- MVP Delivery Plan: target-release capability subset and gates when materially changed.

Master Product Document changes only if product semantics/constitutional principles change. The current visual foundation and parity-governance clarifications do not require that.

## 8. Continuation rule

A future ChatGPT/Codex session must not depend on chat history. The phrase **“KEFE’yi geliştirmeye devam et”** means:
1. Read `docs/status/CURRENT.md` from `main` and root `AGENTS.md`.
2. Inspect current open PR stack, top PR head, recent merges and CI before acting.
3. Resolve the top accepted/verified working checkpoint; distinguish verified runtime SHA from later docs-only head.
4. Read relevant ADR/executable contract and Drive CURRENT/WORKING authority where needed.
5. Determine whether the next unresolved work is visual, non-visual architecture/runtime, release evidence or an accepted-later capability; do not assume “remaining work = UI polish”.
6. Continue in dependency order; do not restart product analysis.
7. Ask the user only when a material product/architecture decision is genuinely unresolved; do not ask for already-known repo/history context.
8. Contract first for boundary changes; runtime second; tests/CI/evidence with implementation.
9. Never merge out of stack order or treat preview as production fallback.
10. Never claim PASS without the required evidence.

This rule should be reflected in the canonical `docs/status/CURRENT.md` handoff on main and kept current after meaningful milestones.
