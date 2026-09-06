# Secondary and unintended consequences simulator — 2026-09-01

Status: IMPLEMENTATION CANDIDATE / EXACT-HEAD CI PENDING / NO CAPABILITY PROMOTION

Issue: #437  
Capability: CAP-022 (`ROADMAP_ACCEPTED`)  
Stack base: `feature/insufficient-info-response` (`e665ec9b`)

ADR: ADR-0180  
Contract: `docs/contracts/unintended-consequences.v1.json`

## User-visible outcome

Users can inspect simulated second- and third-order ripple effects via `UnintendedConsequencesCard`:
- Ripple categories: `PERVERSE_INCENTIVE` (Cobra effect), `MARKET_DISTORTION`, `BEHAVIORAL_REBOUND` (Jevons paradox), `SYSTEMIC_DISPLACEMENT`.
- Overall systemic risk rating: `LOW_DRIFT`, `MODERATE_IMPACT`, `SEVERE_PARADOX`.
- Mitigation feasibility scoring preventing naive linear policy assumptions.

## Verification & Boundary

- Contract: `docs/contracts/unintended-consequences.v1.json` (PASS);
- ADR: `docs/adr/0180-secondary-and-unintended-consequences-simulator.md` (PASS);
- Backend consequences simulator & ripple evaluation tests: `services/api/tests/test_unintended_consequences.py` (PASS);
- Mobile presentation card & domain model tests: `apps/mobile/test/unintended_consequences_test.dart` (PASS);
- Second-order systemic modeling invariant: PASS.

## Lifecycle

CAP-022 remains `ROADMAP_ACCEPTED` pending case authoring pipeline integration of systemic ripple scenarios.
