# Proportionality and least intrusive means engine — 2026-09-01

Status: IMPLEMENTATION CANDIDATE / EXACT-HEAD CI PENDING / NO CAPABILITY PROMOTION

Issue: #441  
Capability: CAP-025 (`ROADMAP_ACCEPTED`)  
Stack base: `feature/insufficient-info-response` (`e665ec9b`)

ADR: ADR-0184  
Contract: `docs/contracts/proportionality-test.v1.json`

## User-visible outcome

Users can inspect the 3 constitutional prongs of proportionality via `ProportionalityCard`:
- Three-prong evaluation: Suitability (`suitability_score`), Necessity / Least Intrusive Means (`necessity_least_intrusive_score`), and Strict Proportionality (`strict_proportionality_score`).
- Constitutional outcome: `PROPORTIONAL_VALID`, `EXCESSIVELY_BURDENSOME`, `DISPROPORTIONATE_INVALID`.
- Enforces modern constitutional law standards against arbitrary overreach.

## Verification & Boundary

- Contract: `docs/contracts/proportionality-test.v1.json` (PASS);
- ADR: `docs/adr/0184-proportionality-and-least-intrusive-means-engine.md` (PASS);
- Backend proportionality calculator & tripartite weighting tests: `services/api/tests/test_proportionality_test.py` (PASS);
- Mobile presentation card & domain model tests: `apps/mobile/test/proportionality_test.dart` (PASS);
- Tripartite proportionality invariant: PASS.

## Lifecycle

CAP-025 remains `ROADMAP_ACCEPTED` pending case authoring pipeline calibration of least-intrusive alternative libraries.
