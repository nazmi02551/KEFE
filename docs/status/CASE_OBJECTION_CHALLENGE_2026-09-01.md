# Case objection and challenge engine — 2026-09-01

Status: IMPLEMENTATION CANDIDATE / EXACT-HEAD CI PENDING / NO CAPABILITY PROMOTION

Issue: #429  
Capability: CAP-068 (`ROADMAP_ACCEPTED`)  
Stack base: `feature/insufficient-info-response` (`e665ec9b`)

ADR: ADR-0172  
Contract: `docs/contracts/case-objection-challenge.v1.json`

## User-visible outcome

Citizens, researchers, and stakeholders can file structured objections to any case via `CaseObjectionDialog`:
- Reason taxonomy: `EDITORIAL_BIAS_FRAMING`, `FACTUAL_INACCURACY`, `EXCLUDED_STAKEHOLDER`, `AMBIGUOUS_OPTIONS`, `DEPRECIATED_CONTEXT`.
- Supporting evidence attachment and detailed rationale requirement.
- Full resolution lifecycle: `SUBMITTED` $\rightarrow$ `UNDER_REVIEW` $\rightarrow$ (`ACCEPTED_CORRECTION_FILED` | `REJECTED_WITH_REASON`).

Ensures non-monopolistic public verification and democratized epistemic integrity in accordance with `KEFE-TIM-001`.

## Verification & Boundary

- Contract: `docs/contracts/case-objection-challenge.v1.json` (PASS);
- ADR: `docs/adr/0172-case-objection-and-challenge-engine.md` (PASS);
- Backend objection service & lifecycle resolution tests: `services/api/tests/test_case_objection.py` (PASS);
- Mobile presentation dialog & domain model tests: `apps/mobile/test/case_objection_test.dart` (PASS);
- Structured challenge taxonomy invariant: PASS.

## Lifecycle

CAP-068 remains `ROADMAP_ACCEPTED` pending Admin Studio community challenge triage queue integration.
