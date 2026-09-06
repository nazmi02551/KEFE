# Expert testimony and institutional endorsement engine — 2026-09-01

Status: IMPLEMENTATION CANDIDATE / EXACT-HEAD CI PENDING / NO CAPABILITY PROMOTION

Issue: #439  
Capability: CAP-044 (`ROADMAP_ACCEPTED`)  
Stack base: `feature/insufficient-info-response` (`e665ec9b`)

ADR: ADR-0182  
Contract: `docs/contracts/expert-institutional-testimony.v1.json`

## User-visible outcome

Users can distinguish between scientific consensus, regulatory statements, and corporate lobbying via `ExpertTestimonyCard`:
- Archetype taxonomy: `INDEPENDENT_ACADEMIC_EXPERT`, `GOVERNMENTAL_REGULATORY_BODY`, `INDUSTRY_CORPORATE_STAKEHOLDER`, `CIVIL_SOCIETY_ADVOCATE`.
- Epistemic authority tiers: `HIGH_PEER_REVIEWED`, `OFFICIAL_REGULATORY`, `PARTISAN_SPECIAL_INTEREST`.
- Mandated conflict-of-interest transparency index.

## Verification & Boundary

- Contract: `docs/contracts/expert-institutional-testimony.v1.json` (PASS);
- ADR: `docs/adr/0182-expert-testimony-and-institutional-endorsement-engine.md` (PASS);
- Backend expert testimony service & epistemic tier assignment tests: `services/api/tests/test_expert_testimony.py` (PASS);
- Mobile presentation card & domain model tests: `apps/mobile/test/expert_testimony_test.dart` (PASS);
- Non-astroturfing guarantee invariant: PASS.

## Lifecycle

CAP-044 remains `ROADMAP_ACCEPTED` pending case authoring pipeline calibration of institutional registries.
