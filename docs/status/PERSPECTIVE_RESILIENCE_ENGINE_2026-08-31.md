# Counter-perspective resilience and attitude shift engine — 2026-08-31

Status: IMPLEMENTATION CANDIDATE / EXACT-HEAD CI PENDING / NO CAPABILITY PROMOTION

Issue: #410  
Capability: CAP-116 (`ROADMAP_ACCEPTED`)  
Stack base: `feature/insufficient-info-response` (`e665ec9b`)

ADR: ADR-0153  
Contract: `docs/contracts/counter-perspective-resilience.v1.json`

## User-visible outcome

The KEFE analytics pipeline now provides a counter-perspective resilience engine that evaluates how exposure to opposing arguments impacts deliberation:
- `resilience_index`: Proportion of participants whose stance remains stable after examining peer counter-views.
- `attitude_shift_rate`: Proportion of participants who revised their decision or confidence level post-deliberation.

Zero individual psychometric, political, or ideological profiling is performed.

## Verification & Boundary

- Contract: `docs/contracts/counter-perspective-resilience.v1.json` (PASS);
- ADR: `docs/adr/0153-counter-perspective-resilience-and-attitude-shift-engine.md` (PASS);
- Backend calculation tests: `services/api/tests/test_perspective_resilience_analytics.py` (PASS);
- Strict privacy invariant enforcement: PASS.

## Lifecycle

CAP-116 remains `ROADMAP_ACCEPTED` pending deployment to warehouse reporting pipelines.
