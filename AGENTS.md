# KEFE Agent / Continuation Instructions

This file defines stable repository-working rules for ChatGPT, Codex and other engineering agents. It is an operational instruction layer, not a product specification and not a substitute for canonical product documents.

## 1. Resume instead of restarting

When the user says **“KEFE’yi geliştirmeye devam et”** or equivalent, do not ask them to restate repository history or past decisions.

Before acting:
1. Read `docs/status/CURRENT.md` from `main`.
2. Read `docs/roadmap/CAPABILITY_PORTFOLIO.md`, `docs/roadmap/capability-portfolio.v1.tsv` and the latest capability-portfolio status record.
3. Inspect live repository metadata, open PR stack, top PR/head, recent merges and CI.
4. Resolve the latest exact repo-verified runtime separately from any later documentation-only head.
5. Read the relevant ADR, executable contract and status record for the next unresolved slice.
6. Consult Drive CURRENT/WORKING authority when normative publication detail is needed.
7. Continue in dependency order from durable state.

Chat history is supplementary context only; it is never the engineering source of truth.

## 2. Authority order

Use this order when sources appear inconsistent:
1. accepted constitutional/product authority in the published documentation baseline;
2. accepted ADRs and executable contracts for active implementation boundaries;
3. live GitHub code, migrations, tests and CI evidence;
4. `docs/status/CURRENT.md` continuation summary;
5. Product Bible lifecycle register and its machine-readable GitHub mirror;
6. Drive WORKING checkpoint for unpromoted working deltas;
7. chat history and informal notes.

The portfolio mirror preserves lifecycle and traceability; it cannot silently promote a Proposal, Test, Roadmap or Validation entry. Do not silently promote WORKING over CURRENT.

## 3. Capability portfolio / no-forgotten-feature gate

The Product Bible Roadmap Capability Register is mirrored in `docs/roadmap/capability-portfolio.v1.tsv`. Every material capability has a stable `CAP-*` identity, lifecycle status, phase, priority, owner documents, dependencies, evidence and next gate.

Before selecting or opening a material slice:
- audit unresolved P0/P1 capabilities against live code, ADRs, contracts, status records and CI;
- identify the capability or capabilities advanced by the work;
- reference those `CAP-*` IDs in the issue and PR, or explicitly declare `maintenance-only` scope;
- preserve the recorded lifecycle status unless an explicit product decision updates the owning documents;
- do not treat a proposal or roadmap entry as accepted merely because implementation is convenient;
- update current evidence and next gate when a capability advances;
- use `IMPLEMENTED_VERIFIED` only with exact contract-appropriate evidence;
- do not infer human usability, editorial acceptance, production provider delivery, store compliance or deployed SLO from CI;
- reconcile the Product Bible register and GitHub mirror with zero unexplained drift at documentation milestones.

Run `python scripts/validate_capability_portfolio.py` whenever the portfolio or continuation rules change. A failing portfolio gate blocks the documentation/governance change.

## 4. Core invariants

Preserve unless an explicit accepted decision changes them:
- Commit First;
- Blind First / pre-result isolation where applicable;
- immutable published CaseVersion;
- case-agnostic generic runtime and composition over named Case types;
- preview/production isolation; preview fixtures never production fallback;
- no pre-Commit collective/result/Perspective leakage;
- My KEFE is observed/descriptive only; no personality, ideology, psychometric, bias or causal inference;
- Collective Result is not automatically Signal, truth or authority;
- Signal/Impact do not silently broaden;
- raw backend/CaseVersion values remain unchanged by display localization;
- AI/provider output is not truth authority, editorial acceptance or autonomous publication.

## 5. Contract first

A product, domain or architecture boundary change requires an ADR and machine-readable/executable contract before runtime implementation.

Do not create an ADR for ordinary internal refactoring that does not alter a contracted boundary. Do not use implementation convenience to reopen settled product decisions.

If a genuinely material decision is unresolved or conflicts with canonical authority, stop at the decision boundary and present the conflict/options to the user. Do not guess or rush a product decision.

## 6. Vertical-slice discipline

- Prefer meaningful vertical slices over cosmetic micro-commits.
- One coherent branch/PR per slice.
- Respect the current stacked PR dependency order; never merge a child before its parent.
- PR #68 is excluded from the active MVP/premium stack unless explicitly reviewed separately.
- Before a merge, re-read live stack, mergeability, reviews and relevant CI.
- A docs-only status head does not redefine the last verified runtime SHA.
- A capability may span multiple slices; do not claim the whole CAP complete when only one bounded behavior is verified.

## 7. Evidence discipline

Never call work PASS/completed solely because code exists.

For a runtime checkpoint, use the workflow/evidence requirements of its contract. Current premium checkpoints normally require the same exact runtime SHA to succeed in:
- API CI;
- Mobile CI;
- MVP Beta Gates;
- Global Readiness.

Also enforce applicable format, analyzer, tests, contract, visual, accessibility and performance gates.

Never fabricate or infer from CI:
- human usability or visual approval;
- editorial CQB acceptance;
- production OTP/provider deliverability;
- Apple/Google store compliance;
- deployed production SLO/load/observability;
- operator-validated rollback/switch controls.

Internal Product Preview APK is not a production/store release.

## 8. APK discipline

Do not generate or distribute a new APK for every small change. Produce a phone artifact only for a meaningful exact-head verified checkpoint.

When reviewing visual work, verify that the governed screen is actually reachable from the distributed preview artifact. Source-level existence alone is not sufficient review evidence.

Before presenting a phone candidate as the current implemented phone experience:
- record exact runtime, required workflow evidence, artifact ID/digest and APK hash;
- inventory production and Product Preview routes/surfaces;
- classify implemented consumer surfaces as production+preview, production-only, preview-only or conditional;
- record Preview provider/fixture substitutions separately;
- ensure no intended review surface is silently omitted;
- mark behavior that Preview cannot prove, including provider delivery, production networking/SLO and store behavior.

Product Preview may expose safe review-only navigation, but it must not change production semantics and its fixtures/adapters must never become production fallback.

## 9. Visual system and localization

- dark-first premium KEFE identity with a valid light theme;
- semantic design tokens/surfaces, not raw screen-local styling;
- Rules/Rights cyan-blue, Empathy/Compassion warm gold/coral, gold as signature accent, burgundy secondary;
- accessibility and Reduce Motion by default;
- low-end Android performance is first-class;
- avoid mandatory heavy continuously rendered 3D, WebView or Three.js;
- use reusable provider-neutral visual/media composition and optimized assets;
- concept references are art direction, not runtime evidence or pixel-exact specifications;
- Turkish and English are the currently enabled app locales;
- use governed locale catalogs/resolvers and do not reintroduce presentation-level language branching;
- unsupported lookup has deterministic English fallback but does not imply locale support;
- display localization must not mutate raw domain/backend values.

Read Issue #129 / ADR-0055 / the Slice 17 executable contract for the current high-fidelity foundation plan.

## 10. Documentation lifecycle

- Update `docs/status/CURRENT.md` after meaningful mainline/handoff changes.
- Record unpromoted verified deltas in Drive WORKING where appropriate.
- Do not silently overwrite or promote Drive CURRENT.
- Do not create parallel official manifestos when an existing logical document owns the subject.
- At documentation milestones, propagate accepted changes to the owning Product Bible, Master, Design System, Engineering Blueprint and other existing documents.
- Regenerate DOCX/PDF artifacts, run render/accessibility/manifest/checksum QA, upload durably and verify readback before calling publication PASS.
- Commercial, analytics, statistical methodology, reporting, research, FinOps, Signal and Impact capabilities are product-completeness concerns and must not disappear merely because the current slice is consumer-facing.

## 11. Communication

While executing multi-step work, give brief progress updates. Be explicit about:
- current runtime SHA versus docs-only head;
- CI evidence versus pending evidence;
- capability IDs and the bounded advancement being made;
- assumptions and unresolved decisions.

Do not make the user manually reconstruct state that the repository, capability register and Drive can provide.
