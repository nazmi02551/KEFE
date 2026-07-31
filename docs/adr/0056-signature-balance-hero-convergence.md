# ADR-0056 — Signature Balance Hero Convergence

**Status:** Accepted working architecture  
**Date:** 2026-07-31  
**Tracker:** #137  
**Parent:** ADR-0055 High-Fidelity Visual Composition Foundation

## Context

Slice 17 established a reusable provider-neutral visual-composition foundation and phone surface-parity discipline. The current two-option decision UI already contains `KefeBalanceVisual`, but it is a lightweight stylized illustration rather than the signature premium KEFE hero quality expressed by the target concept references.

The next adoption slice must produce a visually obvious improvement without changing decision semantics, exposing collective information before Commit, creating named-Case runtime branches, or requiring heavy continuous 3D rendering.

The primary consumer target is the existing generic two-option `SINGLE_CHOICE` decision capability rendered by `QuestionInputCard`. The current raw response remains one of the two canonical option values. A visual tilt/highlight represents selection state only; it is not a percentage, confidence score, population distribution or methodology output.

## Decision

Create a reusable **Signature Balance Hero** presentation for generic two-option decision questions.

### 1. Eligibility is capability-driven

The signature balance treatment is eligible when:
- the current question response type is `SINGLE_CHOICE`;
- exactly two canonical options exist;
- the existing generic decision renderer is active.

Eligibility must not inspect Case ID, Case title, domain-specific names or manually enumerated Cases.

### 2. Preserve response semantics

The hero has three display states:
- neutral — no option selected;
- left selected — visual beam/pan emphasis leans toward canonical option 0;
- right selected — visual beam/pan emphasis leans toward canonical option 1.

No percentage, continuous coordinate or crowd/collective value may be invented for a binary decision. A future scalar/continuous decision capability may define its own contract and reuse visual primitives later.

### 3. Presentation composition

Use lightweight Flutter-native composition as the initial renderer:
- layered CustomPainter geometry for stand, beam, chains and pans;
- theme-adaptive metallic/gold material gradients;
- Rules/Rights cyan emphasis for the left side;
- Empathy/Compassion warm emphasis for the right side;
- deterministic ambient glow/highlight and depth cues;
- no continuously running animation;
- motion only on explicit selection state transition and resolved through Slice 17 Reduce Motion policy.

The renderer may later gain a governed optimized static/pre-rendered base asset without changing question semantics or the public widget contract.

### 4. Interaction remains accessible and explicit

The hero itself is semantic visual feedback. Existing explicit option controls remain tappable, keyboard/screen-reader understandable and independently testable.

Do not make precise pan artwork the sole means of choosing an answer. Option labels remain readable text outside/adjacent to the drawn geometry and continue to emit canonical backend values unchanged.

### 5. Visual layout

The expanded hero should:
- create a strong vertical focal area on normal phones;
- compact deterministically on narrow/short viewports;
- avoid clipping at supported text scales;
- keep labels outside unsafe painted detail areas;
- use Slice 17 visual roles/policies rather than local hard-coded dark-only colors;
- preserve light theme validity.

### 6. Commit First / Blind First

The pre-Commit hero may display only:
- the current Case/question copy already permitted pre-Commit;
- the user’s own current selection state;
- decorative KEFE visual vocabulary.

It must not display:
- collective percentages;
- consensus;
- Perspective;
- inferred community position;
- expert/segment/country results;
- Signal or Impact.

### 7. Performance and motion

- No WebView, Three.js or mandatory live 3D engine.
- Custom painting must remain bounded and avoid per-frame work when idle.
- Repaint only when relevant visual state/theme/size changes.
- Selection transitions use bounded duration through shared Reduce Motion policy.
- No particle loop or continuous shader animation.

### 8. Preview and production parity

Production and Product Preview must reuse the same Signature Balance widget for the same generic two-option capability. Preview may supply deterministic Case data/repositories but may not own a separate balance implementation.

The phone candidate must prove a two-option decision path reaches the Signature Balance Hero before Commit.

## Consequences

### Positive
- First visibly distinctive KEFE hero is introduced without product-semantic debt.
- Later Case families can receive the balance automatically when they use the same capability.
- Accessibility and low-end Android constraints remain intact.
- Target art direction becomes materially closer while preserving generic runtime architecture.

### Trade-offs
- Flutter-native painting will be more dimensional than the current visual but may still not equal final photorealistic concept art. A later asset-rendition improvement can replace the base artwork behind the same contract.
- Binary selection cannot honestly reproduce concept mockups that show continuous percentages; fidelity must not override truthfulness.

## Rejected alternatives

### Named Case hero branches
Rejected because they violate the case-agnostic architecture.

### Convert binary questions to a percentage slider
Rejected because it changes product/data semantics solely for visual similarity.

### Continuous 3D renderer
Rejected for low-end Android, accessibility, complexity and energy-cost reasons.

### Preview-only rich balance
Rejected because visual review would not represent the production presentation path.

## Verification

The slice is not complete until exact-head required CI passes and tests cover:
- eligibility only for exactly-two-option `SINGLE_CHOICE`;
- canonical option values unchanged;
- neutral/left/right visual states;
- no collective/pre-Commit leakage;
- Reduce Motion;
- light/dark and compact layout;
- semantics/explicit option controls;
- Product Preview reachability using the production widget;
- existing Decision/Commit/Reveal regressions.

Human visual approval remains external evidence.