# Verified institution response and impact room — 2026-08-31

Status: IMPLEMENTATION CANDIDATE / EXACT-HEAD CI PENDING / NO CAPABILITY PROMOTION

Issue: #406  
Capability: CAP-050 (`ROADMAP_ACCEPTED`)  
Stack base: `feature/insufficient-info-response` (`e665ec9b`)

ADR: ADR-0149  
Contract: `docs/contracts/institution-response.v1.json`

## User-visible outcome

When a community Signal reaches maturity, users can view verified responses from target public/private institutions in the Impact room.

Responses are categorized by intent (`ACKNOWLEDGE`, `COMMITMENT`, `POLICY_CHANGE`, `FACTUAL_CLARIFICATION`, `DECLINE_WITH_REASON`) and carry an official verified authority badge, statement text, and optional target milestone date.

## Verification & Boundary

- Contract: `docs/contracts/institution-response.v1.json` (PASS);
- ADR: `docs/adr/0149-verified-institution-response-and-impact-room.md` (PASS);
- Backend impact service & models: `services/api/src/kefe_api/modules/impact/` (PASS);
- Mobile presentation card & domain models: `apps/mobile/lib/features/impact/` (PASS);
- Turkish & English localization catalogs: PASS;
- Unit tests: `services/api/tests/test_institution_response.py` & `apps/mobile/test/institution_response_test.dart` (PASS).

## Lifecycle

CAP-050 remains `ROADMAP_ACCEPTED` pending live institutional authority onboarding.
