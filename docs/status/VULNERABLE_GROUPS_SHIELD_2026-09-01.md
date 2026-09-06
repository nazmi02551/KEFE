# Vulnerable groups protection shield — 2026-09-01

Status: IMPLEMENTATION CANDIDATE / EXACT-HEAD CI PENDING / NO CAPABILITY PROMOTION

Issue: #442  
Capability: CAP-026 (`ROADMAP_ACCEPTED`)  
Stack base: `feature/insufficient-info-response` (`e665ec9b`)

ADR: ADR-0185  
Contract: `docs/contracts/vulnerable-groups-shield.v1.json`

## User-visible outcome

Users can inspect the impact of options on marginalized and fragile demographics via `VulnerableGroupsShieldCard`:
- Cohort breakdown: `CHILDREN_YOUTH`, `ELDERLY_GERIATRIC`, `LOW_INCOME_IMPOVERISHED`, `PERSONS_WITH_DISABILITIES`, `MINORITY_MARGINALIZED`.
- Protection status: `STRONG_PROTECTIVE_FLOOR`, `NEUTRAL_NO_DISPROPORTION`, `SEVERE_DISPROPORTIONATE_BURDEN`.
- Rawlsian Maximin safety net floor score ($[0.0, 1.0]$).

## Verification & Boundary

- Contract: `docs/contracts/vulnerable-groups-shield.v1.json` (PASS);
- ADR: `docs/adr/0185-vulnerable-groups-protection-shield.md` (PASS);
- Backend vulnerable groups shield calculator & Maximin floor tests: `services/api/tests/test_vulnerable_groups_shield.py` (PASS);
- Mobile presentation card & domain model tests: `apps/mobile/test/vulnerable_groups_shield_test.dart` (PASS);
- Rawlsian safety floor invariant: PASS.

## Lifecycle

CAP-026 remains `ROADMAP_ACCEPTED` pending case authoring pipeline integration of vulnerable cohort demographic impact datasets.
