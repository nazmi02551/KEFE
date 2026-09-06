# ADR-0157: Dual-Theme Contrast and Reduce-Motion Accessibility Contract (CAP-077)

## Status

ACCEPTED

## Context

KEFE is designed as a universal civic deliberation platform. Accessibility across diverse age groups, visual impairments, vestibular sensitivities, and lower-tier mobile hardware is a fundamental constitutional requirement.

## Decision

1. **Dual-Theme Contrast Invariants**:
   - Both Dark (`0xFF050811`) and Light (`0xFFF4F6FA`) semantic themes must enforce minimum WCAG 2.1 AA ($4.5:1$) contrast ratios for regular text (`foreground` vs `canvas`/`surface`) and large text/headers ($3:1$).
   - Critical semantic cues (`rules`, `empathy`, `gold`, `attention`, `success`) must maintain legible contrast on both themes.
2. **Reduce-Motion By Default**:
   - When the user's OS specifies `MediaQuery.disableAnimations` or `reduce-motion: reduce`, all page transitions, card reveals, and progress bars must render statically or complete in $\le 50\text{ms}$.
3. **Hardware Performance Invariant**:
   - No continuous Three.js/3D rendering loops or mandatory WebViews on core deliberation screens, guaranteeing 60fps performance on low-end devices.

## Consequences

- Full WCAG 2.1 compliance.
- Inclusive and pleasant experience for all citizens regardless of device or visual acuity.
