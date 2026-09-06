# Threshold sensitivity analysis engine — 2026-08-31

Status: IMPLEMENTATION CANDIDATE / EXACT-HEAD CI PENDING / NO CAPABILITY PROMOTION

Issue: #422  
Capability: CAP-018 (`ROADMAP_ACCEPTED`)  
Stack base: `feature/insufficient-info-response` (`e665ec9b`)

ADR: ADR-0165  
Contract: `docs/contracts/threshold-sensitivity-analysis.v1.json`

## User-visible outcome

Users and policymakers can explore how decision consensus shifts across quantitative variables through the `ThresholdAnalysisCard`:
- Discrete acceptance curve mapping across quantitative steps (e.g. monetary fees, speed limits, age thresholds).
- Identification of the exact `tipping_point_threshold` where collective acceptance crosses the 50% majority line.

## Verification & Boundary

- Contract: `docs/contracts/threshold-sensitivity-analysis.v1.json` (PASS);
- ADR: `docs/adr/0165-threshold-sensitivity-analysis-engine.md` (PASS);
- Backend sensitivity calculator & tipping point tests: `services/api/tests/test_threshold_analysis.py` (PASS);
- Mobile presentation card & domain model tests: `apps/mobile/test/threshold_analysis_test.dart` (PASS);
- Monotonic continuum support invariant: PASS.

## Lifecycle

CAP-018 remains `ROADMAP_ACCEPTED` pending interactive parametric slider question composer integration.
