# KEFE Agent / Continuation Instructions

This file defines stable repository-working rules for ChatGPT, Codex and other engineering agents. It is an operational instruction layer, not a product specification and not a substitute for canonical product documents.

## 1. Resume instead of restarting

When the user says **“KEFE’yi geliştirmeye devam et”** (or equivalent), do not ask them to restate repository history or past decisions.

Before acting:
1. Read `docs/status/CURRENT.md` from `main`.
2. Inspect live repository metadata, open PR stack, top PR/head, recent merges and CI.
3. Resolve the latest exact repo-verified runtime separately from any later documentation-only head.
4. Read the relevant ADR, executable contract and status record for the next unresolved slice.
5. Consult Drive CURRENT/WORKING authority when normative publication detail is needed.
6. Continue in dependency order from durable state.

Chat history is supplementary context only; it is never the engineering source of truth.

## 2. Authority order

Use this order when sources appear inconsistent:
1. accepted constitutional/product authority in the published documentation baseline;
2. accepted ADRs + executable contracts for active implementation boundaries;
3. live GitHub code, migrations, tests and CI evidence;
4. `docs/status/CURRENT.md` continuation summary;
5. Drive WORKING checkpoint for unpromoted working deltas;
6. chat history / informal notes.

Do not silently promote WORKING over CURRENT.

## 3. Core invariants

Preserve unless an explicit accepted decision changes them:
- Commit First.
- Blind First / pre-result isolation where applicable.
- immutable published CaseVersion.
- case-agnostic generic runtime; composition over named Case types.
- preview/production isolation; preview fixtures never production fallback.
- no pre-Commit collective/result/Perspective leakage.
- My KEFE is observed/descriptive only; no personality, ideology, psychometric, bias or causal inference.
- Signal/Impact do not silently broaden.
- raw backend/CaseVersion values remain unchanged by display localization.
- AI/provider output is not truth authority, editorial acceptance or autonomous publication.

## 4. Contract first

A product/domain/architecture boundary change requires an ADR and machine-readable/executable contract before runtime implementation.

Do not create an ADR for ordinary internal refactoring that does not alter a contracted boundary. Do not use implementation convenience to reopen settled product decisions.

If a genuinely material decision is unresolved or conflicts with canonical authority, stop at the decision boundary and present the conflict/options to the user. Do not guess or rush a product decision.

## 5. Vertical-slice discipline

- Prefer meaningful vertical slices over cosmetic micro-commits.
- One coherent branch/PR per slice.
- Respect the current stacked PR dependency order; never merge a child before its parent.
- PR #68 is excluded from the active MVP/premium stack unless explicitly reviewed separately.
- Before a merge, re-read live stack, mergeability, reviews and relevant CI.
- A docs-only status head does not redefine the last verified runtime SHA.

## 6. Evidence discipline

Never call work PASS/completed solely because code exists.

For a runtime checkpoint, use the workflow/evidence requirements of its contract. Current premium checkpoints normally require the same exact runtime SHA to succeed in:
- API CI
- Mobile CI
- MVP Beta Gates
- Global Readiness

Also enforce applicable format/analyzer/tests/contract/visual/accessibility/performance gates.

Never fabricate or infer from CI:
- human usability or visual approval;
- editorial CQB acceptance;
- production OTP/provider deliverability;
- Apple/Google store compliance;
- deployed production SLO/load/observability;
- operator-validated rollback/switch controls.

Internal Product Preview APK ≠ production/store release.

## 7. APK discipline

Do not generate/distribute a new APK for every small change. Produce a phone artifact only for a meaningful exact-head verified checkpoint.

When reviewing visual work, verify that the governed screen is actually reachable from the distributed preview artifact. Source-level existence alone is not sufficient review evidence.

A phone candidate may be described as the current implemented phone experience only for its exact verified runtime SHA. Before presenting it that way, audit production versus Product Preview surface reachability at that SHA:
- inventory the production routes/user-facing surfaces;
- inventory the Product Preview routes/user-facing surfaces;
- classify every implemented consumer surface as production+preview reachable, production-only with reason, preview-only with reason, or conditional/feature-gated with an explicit review path/exclusion;
- record Product Preview provider/fixture substitutions separately from production providers;
- ensure no intended review surface is silently omitted from the artifact;
- mark behaviors that preview cannot prove, including real provider delivery, production networking/SLO, store behavior and other external evidence.

Product Preview may expose safe review-only navigation, but it must not change production semantics and its fixtures/adapters must never become production fallback.

## 8. Visual-system direction

- dark-first premium KEFE identity with valid light theme;
- semantic design tokens/surfaces, not raw screen-local styling;
- Rules/Rights cyan-blue, Empathy/Compassion warm gold/coral, gold as signature accent, burgundy secondary;
- accessibility and Reduce Motion by default;
- low-end Android performance is first-class;
- avoid mandatory heavy continuously rendered 3D, WebView or Three.js;
- high-fidelity art direction should use reusable provider-neutral visual/media composition, optimized assets where appropriate and lightweight Flutter overlays;
- concept references are target art direction, not runtime evidence or pixel-exact specifications.

Read Issue #129 / ADR-0055 / the Slice 17 executable contract for the current high-fidelity foundation plan.

## 9. Localization

- Turkish and English are the currently enabled app locales.
- Use governed locale catalogs/resolvers; do not reintroduce presentation-level language branching.
- Unsupported resource lookup has deterministic English fallback but does not imply support for that locale.
- Display localization must not mutate raw domain/backend values.

## 10. Documentation lifecycle

- Update `docs/status/CURRENT.md` after meaningful mainline/handoff changes so a new session can recover correctly.
- Record unpromoted verified deltas in Drive WORKING where appropriate.
- Do not silently overwrite Drive CURRENT.
- Do not create parallel official manifestos when an existing logical document owns the subject.
- At declared documentation milestones, propagate accepted changes to the owning Product Bible / Design System / Engineering Blueprint / other existing documents, regenerate publication artifacts, run render/QA/manifest/checksum checks, upload durably and verify readback before calling publication PASS.

## 11. Communication

While executing multi-step work, give brief progress updates. Be explicit about:
- current runtime SHA versus docs-only head;
- CI evidence versus pending evidence;
- assumptions and unresolved decisions.

Do not make the user manually reconstruct state that the repository and Drive can provide.
