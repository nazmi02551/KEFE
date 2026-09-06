# Source diversity indicator and spectrum engine — 2026-09-01

Status: IMPLEMENTATION CANDIDATE / EXACT-HEAD CI PENDING / NO CAPABILITY PROMOTION

Issue: #427  
Capability: CAP-071 (`ROADMAP_ACCEPTED`)  
Stack base: `feature/insufficient-info-response` (`e665ec9b`)

ADR: ADR-0170  
Contract: `docs/contracts/source-diversity-indicator.v1.json`

## User-visible outcome

Users and auditors can inspect the source diversity spectrum of any case via the `SourceDiversityBadge`:
- Diversity classifications: `HIGH_DIVERSITY` (broad pluralistic balance), `BALANCED_DIVERSITY`, `LIMITED_DIVERSITY` (single-sector concentration).
- Breakdown across 5 core pillar domains: `ACADEMIC_SCIENTIFIC`, `OFFICIAL_GOVERNMENT`, `CIVIC_INDEPENDENT`, `MAINSTREAM_JOURNALISM`, `TECHNICAL_INDUSTRY`.

Prevents informational monocultures and upholds KEFE-TIM-001 integrity standards.

## Verification & Boundary

- Contract: `docs/contracts/source-diversity-indicator.v1.json` (PASS);
- ADR: `docs/adr/0170-source-diversity-indicator-and-spectrum-engine.md` (PASS);
- Backend diversity calculator & dispersion tests: `services/api/tests/test_source_diversity.py` (PASS);
- Mobile presentation badge & domain model tests: `apps/mobile/test/source_diversity_test.dart` (PASS);
- Plurality taxonomy invariant: PASS.

## Lifecycle

CAP-071 remains `ROADMAP_ACCEPTED` pending automated source taxonomy crawler classifier integration.
