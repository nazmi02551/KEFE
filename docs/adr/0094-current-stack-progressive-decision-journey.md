# ADR-0094: Current-Stack Progressive Decision Journey

- Status: Accepted for implementation
- Date: 2026-08-03
- Amended: 2026-08-04 by Issue #283
- Issue: #277
- Runtime base: PR #276 / `fix/installable-phone-preview-artifact`
- Exact base SHA: `a2602b27bf238e7d7e886afa90c9d2acd8338115`
- Capabilities: CAP-001, CAP-008, CAP-009, CAP-031, CAP-035, CAP-095

## Context

The current mobile stack already has a high-fidelity semantic visual system, premium loading/error/action surfaces, accessibility and Reduce Motion behavior, a phone-preview artifact boundary, and generic server-authoritative Flow rendering. The current Decision screen still renders every runtime-supported step in one vertical page. This can make the current task unclear and can combine Context, Decision, Result, Perspectives and Reflection into a long surface.

An earlier candidate implementation in PR #278 was built on PR #118. The current installable phone stack is hundreds of commits ahead and materially changed Decision, Onboarding, Perspective, Reflection, visual composition, reliability and artifact-delivery boundaries. Copying the older screen implementation over the current files would regress the active visual and reliability foundation.

PR #280 established one focused top-level Flow primitive, but its first implementation still rendered every question, the optional ReasonPolicy surface and Commit inside one long `DECISION` column. Issue #283 therefore amends this ADR to define the intended generic card-by-card Decision sub-journey without adding a backend Flow primitive.

## Decision

### 1. Current stack is the implementation authority

The progressive experience will be implemented on PR #276's exact verified phone-preview head. Existing current-stack visual surfaces remain authoritative. New progressive surfaces must use semantic KEFE tokens, `KefeSurface`, `KefeMotion`, the current theme and the existing public feature components.

### 2. Legacy renderer remains intact

The existing `DecisionFlowScreen` remains the legacy long-scroll renderer. A new experience wrapper selects either:

- the current long-scroll screen; or
- a new progressive screen that renders one authoritative runtime step.

The existing two-page `OnboardingGateScreen` also remains intact. A separate experience wrapper selects it or onboarding v2.

This avoids replacing current high-fidelity implementation files with older copies and provides a direct rollback path.

### 3. Runtime-authoritative active step

The progressive Decision screen selects the furthest runtime step whose state is `READY`. When no step is ready, it falls back to the furthest `UNSUPPORTED` step and then the furthest `COMPLETED` step. It does not invent a Case-specific order and does not infer a stage from titles, domains or provider data.

Repeated Decision primitives remain separate because runtime step identity and order remain authoritative.

### 3.1 Presentation-only Decision sub-journey

A `DECISION` runtime primitive is a domain-authoritative envelope, not a requirement to render every input simultaneously. Inside the active `DECISION` primitive, the progressive presentation derives a local sub-journey only from the pinned `DecisionCase.questions` order and its derived `ReasonPolicy`:

1. one focused question stage for each question, preserving CaseVersion order;
2. one optional reason stage only when the CaseVersion enables ReasonPolicy;
3. one final review and Commit stage.

This sub-journey does not create, rename, reorder or complete backend Flow steps. It does not branch on Case title, domain, format or named fixtures. A one-question Case, multi-question Case, optional question, reason-enabled Case and no-reason Case all use the same resolver.

Required questions block forward navigation until answered. Optional questions may be explicitly skipped. The user may navigate backward and edit any visible answer or private reason before Commit. After Commit, the runtime advances normally and the sub-journey is no longer editable.

Draft restoration is deterministic and presentation-only: open the first unanswered required question; otherwise open the first unanswered question that has not been explicitly skipped in the current presentation session; otherwise open ReasonPolicy when enabled; otherwise open review. Persisted answers and private reasons remain owned by the existing controller and draft store. The presentation index itself is not a new domain or persistence field.

The active journey header exposes the actual focused sub-stage and progress within the Decision envelope. It must not pretend that one `DECISION` primitive is one user task when multiple questions and review remain.

### 4. Explicit Context advancement

When a progressive journey exposes an actionable Context step, reading the card does not automatically complete the exposure. The user explicitly chooses **“İnceledim — devam et”**. This records the existing runtime exposure through the existing controller/repository contract and refreshes the runtime. It does not introduce a new domain primitive.

The legacy renderer preserves its existing automatic exposure behavior.

### 5. Result and Perspective disclosure

After Commit, Collective Result becomes the active runtime step. The progressive screen shows the committed result first. Different-perspective cards open only after an explicit user action.

Perspective preparation may happen through the existing post-Commit controller behavior, but no Perspective content is visible before Commit or before the disclosure action. The action does not replay answers, private reasons or Commit.

Independent post-Commit capabilities such as Consensus, community reasons, progress and sharing must not become inaccessible merely because Perspective cards are progressively disclosed.

### 6. Onboarding v2

Onboarding v2 contains three premium pages:

1. **Önce kendi kararını tart.**
2. **Kararının toplumdaki yerini gör.**
3. **Farklı bakışları ve karar yolculuğunu keşfet.**

“Kararının toplumdaki yeri” means a descriptive position in the current question's distribution. It is not the person's social position, worth, identity, ideology, personality or psychometric profile. Reweigh copy may describe observed first/final decision differences but may not claim why a change occurred.

Turkish and English copy remain governed locale resources.

### 7. Runtime selection and rollback

The shared configuration provider defaults to legacy when an app is instantiated directly, preserving existing test and embedding expectations. Production and Product Preview entrypoints explicitly install the environment-selected configuration.

The default built experience enables the new modes. Independent build-time switches restore the previous modes:

- `KEFE_PROGRESSIVE_DECISION_JOURNEY=false`
- `KEFE_ONBOARDING_V2=false`

This is a build-time rollback boundary only. No remote kill switch or operator-validated production rollback is claimed.

### 8. APK boundary

The installable review APK must be produced from `lib/main_preview.dart` through the PR #276 artifact contract. A production-entry APK compiled against an intentionally unconfigured endpoint is not an installable review artifact and must not be handed to the user.

## Invariants

- Commit First and applicable Blind First remain binding.
- Published CaseVersion remains immutable.
- Flow runtime remains generic and authoritative.
- Preview fixtures never become production fallback.
- Result and Perspective remain post-Commit only.
- Private reasons are not replayed or exposed.
- My KEFE remains observed/descriptive only.
- No personality, ideology, psychometric, bias, morality, social-worth or causal inference is introduced.
- Existing controller, repository, retry, idempotency, exposure and Reflection contracts remain unchanged.

## Verification

One exact runtime SHA must pass:

- API CI;
- Mobile CI;
- MVP Beta Gates;
- Global Readiness;
- the installable phone-artifact boundary.

Tests must cover active-step resolution, explicit Context continuation, generic one-question and multi-question Decision sub-journeys, required blocking, optional skipping, ReasonPolicy/no-reason composition, backward navigation, draft restoration, final review/Commit, post-Commit result/Perspective disclosure, onboarding v2 TR/EN copy, legacy Decision rollback, legacy onboarding rollback, accessibility semantics and current phone-preview reachability.

CI does not constitute human visual or usability approval.
