# Temporal retest and drift engine — 2026-09-01

Status: IMPLEMENTATION CANDIDATE / EXACT-HEAD CI PENDING / NO CAPABILITY PROMOTION

Issue: #430  
Capability: CAP-013 (`ROADMAP_ACCEPTED`)  
Stack base: `feature/insufficient-info-response` (`e665ec9b`)

ADR: ADR-0173  
Contract: `docs/contracts/temporal-retest-drift.v1.json`

## User-visible outcome

Users can observe longitudinal drift and conviction shifts in their decisions over time via `TemporalDriftCard`:
- Blind retest execution (no anchoring on previous historical answer until committed).
- Qualitative drift classifications: `STABLE_CONVICTION`, `MATURED_REVISION`, `EXPLORATORY_SHIFT`, `REINFORCED_CERTAINTY`.
- Descriptive-only reporting preserving My KEFE non-judgmental philosophy.

## Verification & Boundary

- Contract: `docs/contracts/temporal-retest-drift.v1.json` (PASS);
- ADR: `docs/adr/0173-temporal-retest-and-drift-engine.md` (PASS);
- Backend drift calculator & confidence delta tests: `services/api/tests/test_temporal_drift.py` (PASS);
- Mobile presentation card & domain model tests: `apps/mobile/test/temporal_drift_test.dart` (PASS);
- Blind retest invariant: PASS.

## Lifecycle

CAP-013 remains `ROADMAP_ACCEPTED` pending long-tail notification scheduler integration for retest invitations.
