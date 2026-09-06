# What would change my mind inquiry engine — 2026-09-01

Status: IMPLEMENTATION CANDIDATE / EXACT-HEAD CI PENDING / NO CAPABILITY PROMOTION

Issue: #431  
Capability: CAP-010 (`ROADMAP_ACCEPTED`)  
Stack base: `feature/insufficient-info-response` (`e665ec9b`)

ADR: ADR-0174  
Contract: `docs/contracts/what-would-change-my-mind.v1.json`

## User-visible outcome

Users reflect on counterfactual pivot conditions that would falsify or alter their decision via `ChangeMindInquiryCard`:
- Counterfactual condition archetypes: `EMPIRICAL_DATA_THRESHOLD`, `VULNERABILITY_PROTECTION`, `ECONOMIC_SUSTAINABILITY`, `MORAL_IMPASSE_EMPATHY`, `UNCONDITIONAL_STANCE`.
- Epistemic flexibility classifications: `HIGHLY_EPISTEMIC_OPEN`, `CONDITIONALLY_FLEXIBLE`, `CATEGORICAL_ABSOLUTE`.
- Fosters self-awareness and diminishes ideological entrenchment.

## Verification & Boundary

- Contract: `docs/contracts/what-would-change-my-mind.v1.json` (PASS);
- ADR: `docs/adr/0174-what-would-change-my-mind-engine.md` (PASS);
- Backend inquiry evaluator & flexibility classification tests: `services/api/tests/test_change_mind_inquiry.py` (PASS);
- Mobile presentation card & domain model tests: `apps/mobile/test/change_mind_inquiry_test.dart` (PASS);
- Non-judgmental reflection invariant: PASS.

## Lifecycle

CAP-010 remains `ROADMAP_ACCEPTED` pending integration into the post-reveal My KEFE deep reflection flow.
