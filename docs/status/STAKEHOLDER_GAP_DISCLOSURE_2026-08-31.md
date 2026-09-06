# Stakeholder Gap disclosure — 2026-08-31

Status: IMPLEMENTATION CANDIDATE / EXACT-HEAD CI PENDING / NO CAPABILITY PROMOTION

Issue: #404  
Capability: CAP-038 (`ROADMAP_ACCEPTED`)  
Stack base: `feature/insufficient-info-response` (`e665ec9b`)

ADR: ADR-0147  
Contract: `docs/contracts/stakeholder-gap-disclosure.v1.json`

## User-visible outcome

When viewing collective dilemma results, users can now see how key stakeholder segments (such as directly affected citizens or domain practitioners) weighed compared to the general community distribution.

Gaps are displayed as clean multi-segment comparative bars with sample size and points differential indicators, strictly after Commit without compromising individual anonymity.

## Verification & Boundary

- Contract: `docs/contracts/stakeholder-gap-disclosure.v1.json` (PASS);
- ADR: `docs/adr/0147-stakeholder-gap-disclosure.md` (PASS);
- Backend calculation & privacy threshold tests: `services/api/tests/test_stakeholder_gap.py` (PASS);
- Mobile visual models & localization tests: `apps/mobile/test/stakeholder_gap_test.dart` (PASS);
- Minimum sample size privacy gate ($n \ge 30$ per segment): PASS.

## Lifecycle

CAP-038 remains `ROADMAP_ACCEPTED` pending end-to-end multi-segment production cohort data ingestion.
