# Long-term future generations projection engine — 2026-09-01

Status: IMPLEMENTATION CANDIDATE / EXACT-HEAD CI PENDING / NO CAPABILITY PROMOTION

Issue: #435  
Capability: CAP-020 (`ROADMAP_ACCEPTED`)  
Stack base: `feature/insufficient-info-response` (`e665ec9b`)

ADR: ADR-0178  
Contract: `docs/contracts/future-generations-projection.v1.json`

## User-visible outcome

Users can inspect the multi-decade intergenerational impacts of options via `FutureGenerationsCard`:
- Horizon projections: `HORIZON_5_YEARS`, `HORIZON_20_YEARS`, `HORIZON_50_YEARS`, `HORIZON_100_YEARS`.
- Aggregated net intergenerational equity score in $[-1.0, 1.0]$.
- Eliminates present-bias temporal discounting in civic deliberation.

## Verification & Boundary

- Contract: `docs/contracts/future-generations-projection.v1.json` (PASS);
- ADR: `docs/adr/0178-long-term-future-generations-projection-engine.md` (PASS);
- Backend projection calculator & multi-horizon weighting tests: `services/api/tests/test_future_generations.py` (PASS);
- Mobile presentation card & domain model tests: `apps/mobile/test/future_generations_test.dart` (PASS);
- Intergenerational justice invariant: PASS.

## Lifecycle

CAP-020 remains `ROADMAP_ACCEPTED` pending case authoring pipeline calibration of multi-decade econometric models.
