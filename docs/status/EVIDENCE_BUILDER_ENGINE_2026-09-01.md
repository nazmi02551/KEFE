# Evidence builder and verification engine — 2026-09-01

Status: IMPLEMENTATION CANDIDATE / EXACT-HEAD CI PENDING / NO CAPABILITY PROMOTION

Issue: #425  
Capability: CAP-098 (`ROADMAP_ACCEPTED`)  
Stack base: `feature/insufficient-info-response` (`e665ec9b`)

ADR: ADR-0168  
Contract: `docs/contracts/evidence-builder.v1.json`

## User-visible outcome

Users can attach and review structured evidence records tied to reasons and deliberation perspectives using `EvidenceItemTile`:
- Categorized source tiers (`ACADEMIC_PEER_REVIEWED`, `OFFICIAL_GOVERNMENT_STAT`, `INVESTIGATIVE_JOURNALISM`, `INSTITUTIONAL_REPORT`).
- Verified quality badges (`EXPERT_AUDITED`, `COMMUNITY_VERIFIED`, `UNVERIFIED`).
- Direct publisher, citation, DOI, and verified URI linking.

Elevates the epistemic quality of arguments and filters out unverified misinformation.

## Verification & Boundary

- Contract: `docs/contracts/evidence-builder.v1.json` (PASS);
- ADR: `docs/adr/0168-evidence-builder-and-verification-engine.md` (PASS);
- Backend evidence service & validation tests: `services/api/tests/test_evidence_builder.py` (PASS);
- Mobile presentation tile & domain model tests: `apps/mobile/test/evidence_builder_test.dart` (PASS);
- Verifiable source reference invariant: PASS.

## Lifecycle

CAP-098 remains `ROADMAP_ACCEPTED` pending community citation audit voting workflow integration.
