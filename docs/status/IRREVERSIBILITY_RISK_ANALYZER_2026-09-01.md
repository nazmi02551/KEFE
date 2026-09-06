# Irreversibility and reversibility risk analyzer — 2026-09-01

Status: IMPLEMENTATION CANDIDATE / EXACT-HEAD CI PENDING / NO CAPABILITY PROMOTION

Issue: #436  
Capability: CAP-021 (`ROADMAP_ACCEPTED`)  
Stack base: `feature/insufficient-info-response` (`e665ec9b`)

ADR: ADR-0179  
Contract: `docs/contracts/irreversibility-risk-analyzer.v1.json`

## User-visible outcome

Users can inspect the structural irreversibility and unwind costs of options via `IrreversibilityRiskCard`:
- Reversibility categories: `FULLY_REVERSIBLE`, `CONDITIONALLY_REVERSIBLE`, `SUBSTANTIALLY_IRREVERSIBLE`, `PERMANENTLY_IRREVERSIBLE`.
- Precautionary risk rating and unwind time projection (in months).
- Enforces the Precautionary Principle to prevent irreversible societal externalities.

## Verification & Boundary

- Contract: `docs/contracts/irreversibility-risk-analyzer.v1.json` (PASS);
- ADR: `docs/adr/0179-irreversibility-and-reversibility-risk-analyzer.md` (PASS);
- Backend reversibility calculator & precautionary weighting tests: `services/api/tests/test_irreversibility_risk.py` (PASS);
- Mobile presentation card & domain model tests: `apps/mobile/test/irreversibility_risk_test.dart` (PASS);
- Precautionary principle invariant: PASS.

## Lifecycle

CAP-021 remains `ROADMAP_ACCEPTED` pending case authoring pipeline calibration of rollback metrics.
