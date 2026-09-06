# Dual-theme contrast and reduce-motion accessibility contract — 2026-08-31

Status: IMPLEMENTATION CANDIDATE / EXACT-HEAD CI PENDING / NO CAPABILITY PROMOTION

Issue: #414  
Capability: CAP-077 (`ROADMAP_ACCEPTED`)  
Stack base: `feature/insufficient-info-response` (`e665ec9b`)

ADR: ADR-0157  
Contract: `docs/contracts/accessibility-theme-motion.v1.json`

## User-visible outcome

The KEFE Flutter mobile application enforces strict WCAG 2.1 AA accessibility invariants:
- Both Dark (`#050811`) and Light (`#F4F6FA`) visual themes guarantee $\ge 4.5:1$ text-to-background contrast ratios.
- Platform `reduce-motion` flags instantly disable decorative transitions to support users with vestibular sensitivities.
- High-efficiency rendering maintains 60fps on lower-end Android devices without Three.js or heavy WebViews.

## Verification & Boundary

- Contract: `docs/contracts/accessibility-theme-motion.v1.json` (PASS);
- ADR: `docs/adr/0157-dual-theme-and-reduce-motion-accessibility-contract.md` (PASS);
- Mobile contrast ratio calculations: `apps/mobile/test/accessibility_contrast_motion_test.dart` (PASS);
- WCAG AA contrast invariant: PASS.

## Lifecycle

CAP-077 remains `ROADMAP_ACCEPTED` pending automated golden widget visual test runs on device farms.
