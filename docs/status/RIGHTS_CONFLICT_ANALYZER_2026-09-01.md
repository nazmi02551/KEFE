# Fundamental rights and liberties conflict analyzer — 2026-09-01

Status: IMPLEMENTATION CANDIDATE / EXACT-HEAD CI PENDING / NO CAPABILITY PROMOTION

Issue: #440  
Capability: CAP-024 (`ROADMAP_ACCEPTED`)  
Stack base: `feature/insufficient-info-response` (`e665ec9b`)

ADR: ADR-0183  
Contract: `docs/contracts/rights-conflict-analyzer.v1.json`

## User-visible outcome

Users can inspect constitutional rights collisions and core essence preservation via `RightsConflictCard`:
- Collision categories: `PRIVACY_VS_SECURITY`, `EXPRESSION_VS_DIGNITY`, `PROPERTY_VS_ENVIRONMENT`, `INDIVIDUAL_LIBERTY_VS_PUBLIC_HEALTH`.
- Constitutional restriction severity: `PERMISSIBLE_RESTRICTION`, `CORE_RIGHT_EROSION`, `UNCONSTITUTIONAL_BREACH`.
- Inalienable core preservation index ($[0.0, 1.0]$).

## Verification & Boundary

- Contract: `docs/contracts/rights-conflict-analyzer.v1.json` (PASS);
- ADR: `docs/adr/0183-fundamental-rights-and-liberties-conflict-analyzer.md` (PASS);
- Backend rights conflict calculator & severity classification tests: `services/api/tests/test_rights_conflict.py` (PASS);
- Mobile presentation card & domain model tests: `apps/mobile/test/rights_conflict_test.dart` (PASS);
- Core essence protection invariant: PASS.

## Lifecycle

CAP-024 remains `ROADMAP_ACCEPTED` pending case authoring pipeline integration of constitutional jurisprudence rubrics.
