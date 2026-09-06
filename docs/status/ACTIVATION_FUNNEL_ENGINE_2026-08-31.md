# Activation funnel aggregation engine — 2026-08-31

Status: IMPLEMENTATION CANDIDATE / EXACT-HEAD CI PENDING / NO CAPABILITY PROMOTION

Issue: #407  
Capability: CAP-115 (`ROADMAP_ACCEPTED`)  
Stack base: `feature/insufficient-info-response` (`e665ec9b`)

ADR: ADR-0150  
Contract: `docs/contracts/activation-funnel.v1.json`

## User-visible outcome

The KEFE analytics pipeline now provides a privacy-preserving activation funnel engine. It computes session milestone progression and drop-off rates across:
1. `WEIGH_STARTED`
2. `DECISION_COMMITTED`
3. `RESULT_REVEALED`
4. `PERSPECTIVE_VIEWED`
5. `DECISION_REVISED`

No raw user choices, reason contents, or psychometric attributes are captured or leaked.

## Verification & Boundary

- Contract: `docs/contracts/activation-funnel.v1.json` (PASS);
- ADR: `docs/adr/0150-activation-funnel-aggregation-engine.md` (PASS);
- Backend calculation & drop-off rate tests: `services/api/tests/test_activation_funnel_analytics.py` (PASS);
- Strict privacy invariant enforcement: PASS.

## Lifecycle

CAP-115 remains `ROADMAP_ACCEPTED` pending deployment to warehouse ingestion jobs.
