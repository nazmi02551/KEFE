# Insufficient information and missing options response — 2026-08-31

Status: IMPLEMENTATION CANDIDATE / EXACT-HEAD CI PENDING / NO CAPABILITY PROMOTION

Issue: #403  
Capability: CAP-011 (`PROPOSAL_REVIEW`)  
Stack base: `feature/account-conversion-validation-recovery` (`091e6329`)

ADR: ADR-0146  
Contract: `docs/contracts/insufficient-info-response.v1.json`

## User-visible outcome

Users facing dilemma questions are no longer forced into artificial binary or predefined single choices. The interface provides two dedicated alternative response actions:
- *Not enough information / Don’t know* (`OPT_OUT_INSUFFICIENT_INFO`)
- *Options are missing / Incomplete choices* (`OPT_OUT_MISSING_OPTIONS`)

Selecting an alternative response allows the user to proceed through the private reason capture and Commit First workflow without distortion.

## Verification & Boundary

- Contract: `docs/contracts/insufficient-info-response.v1.json` (PASS);
- ADR: `docs/adr/0146-insufficient-info-and-missing-options-response.md` (PASS);
- Backend decision service validation tests: `services/api/tests/test_insufficient_info_response.py` (PASS);
- Mobile question input tests and localization tests: `apps/mobile/test/insufficient_info_response_test.dart` (PASS);
- Turkish and English localization catalogs: PASS;
- Capability portfolio validation: `validate_capability_portfolio.py` (PASS).

## Lifecycle

CAP-011 remains `PROPOSAL_REVIEW` until formal external product promotion.
