# Argument strength and validity evaluator — 2026-09-01

Status: IMPLEMENTATION CANDIDATE / EXACT-HEAD CI PENDING / NO CAPABILITY PROMOTION

Issue: #433  
Capability: CAP-041 (`ROADMAP_ACCEPTED`)  
Stack base: `feature/insufficient-info-response` (`e665ec9b`)

ADR: ADR-0176  
Contract: `docs/contracts/argument-strength-validity.v1.json`

## User-visible outcome

Users can inspect the objective dialectical quality of community arguments via `ArgumentStrengthCard`:
- Tri-dimensional breakdown: `empirical_foundation_score`, `logical_consistency_score`, `representative_balance_score`.
- Quality tiers: `TIER_A_ROBUST` ($\ge 0.80$), `TIER_B_PLAUSIBLE` ($[0.50, 0.79]$), `TIER_C_WEAK_RHETORICAL` ($< 0.50$).
- Immunizes deliberation against demagoguery and superficial popularity.

## Verification & Boundary

- Contract: `docs/contracts/argument-strength-validity.v1.json` (PASS);
- ADR: `docs/adr/0176-argument-strength-and-validity-evaluator.md` (PASS);
- Backend strength evaluator & composite weighting tests: `services/api/tests/test_argument_strength.py` (PASS);
- Mobile presentation card & domain model tests: `apps/mobile/test/argument_strength_test.dart` (PASS);
- Tri-dimensional soundness invariant: PASS.

## Lifecycle

CAP-041 remains `ROADMAP_ACCEPTED` pending automated LLM argument grounding scoring integration.
