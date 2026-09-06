# Stakeholder impact matrix engine — 2026-08-31

Status: IMPLEMENTATION CANDIDATE / EXACT-HEAD CI PENDING / NO CAPABILITY PROMOTION

Issue: #423  
Capability: CAP-023 (`ROADMAP_ACCEPTED`)  
Stack base: `feature/insufficient-info-response` (`e665ec9b`)

ADR: ADR-0166  
Contract: `docs/contracts/stakeholder-impact-matrix.v1.json`

## User-visible outcome

Users can inspect the multi-stakeholder burdens and benefits of each policy option via the `StakeholderImpactCard`:
- Impact breakdowns across 5 core stakeholder groups: `DIRECT_USERS`, `WORKERS`, `VULNERABLE_GROUPS`, `TAXPAYERS`, `FUTURE_GENERATIONS`.
- Categorized impact states (`BENEFIT`, `BURDEN`, `NEUTRAL`, `PROTECTION`) with quantified scores (-5 to +5).
- Composite `net_equity_score` preventing majoritarian cost-shifting onto vulnerable groups.

## Verification & Boundary

- Contract: `docs/contracts/stakeholder-impact-matrix.v1.json` (PASS);
- ADR: `docs/adr/0166-stakeholder-impact-matrix-engine.md` (PASS);
- Backend matrix calculation & net equity tests: `services/api/tests/test_stakeholder_impact.py` (PASS);
- Mobile presentation card & domain model tests: `apps/mobile/test/stakeholder_impact_test.dart` (PASS);
- Multi-stakeholder mapping invariant: PASS.

## Lifecycle

CAP-023 remains `ROADMAP_ACCEPTED` pending editorial stakeholder impact template composer integration.
