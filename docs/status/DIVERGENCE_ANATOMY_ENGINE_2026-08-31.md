# Divergence anatomy breakdown engine — 2026-08-31

Status: IMPLEMENTATION CANDIDATE / EXACT-HEAD CI PENDING / NO CAPABILITY PROMOTION

Issue: #420  
Capability: CAP-040 (`ROADMAP_ACCEPTED`)  
Stack base: `feature/insufficient-info-response` (`e665ec9b`)

ADR: ADR-0163  
Contract: `docs/contracts/divergence-anatomy.v1.json`

## User-visible outcome

Users can deconstruct the root drivers of disagreement in complex ethical deliberations via the `DivergenceAnatomyCard`:
- `NORMATIVE_VALUE_WEIGHT`: Fundamental moral/philosophical trade-offs.
- `FACTUAL_PROBABILITY_ASSESSMENT`: Empirical risk and likelihood estimates.
- `PROCEDURAL_GOVERNANCE`: Institutional enforcement and jurisdiction models.
- `TIME_HORIZON`: Generational and temporal discount preferences.

Eliminates toxic intent attribution by clarifying the structured cognitive reasons behind diverging votes.

## Verification & Boundary

- Contract: `docs/contracts/divergence-anatomy.v1.json` (PASS);
- ADR: `docs/adr/0163-divergence-anatomy-breakdown-engine.md` (PASS);
- Backend anatomy calculator & share percentage tests: `services/api/tests/test_divergence_anatomy.py` (PASS);
- Mobile presentation card & domain models: `apps/mobile/test/divergence_anatomy_test.dart` (PASS);
- Neutral cognitive driver taxonomy invariant: PASS.

## Lifecycle

CAP-040 remains `ROADMAP_ACCEPTED` pending driver weighting extraction model integration.
