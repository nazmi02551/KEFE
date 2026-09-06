# Case correction and version history engine — 2026-09-01

Status: IMPLEMENTATION CANDIDATE / EXACT-HEAD CI PENDING / NO CAPABILITY PROMOTION

Issue: #428  
Capability: CAP-072 (`ROADMAP_ACCEPTED`)  
Stack base: `feature/insufficient-info-response` (`e665ec9b`)

ADR: ADR-0171  
Contract: `docs/contracts/case-correction-history.v1.json`

## User-visible outcome

Users can inspect full editorial version changes for any published case via the `CorrectionHistorySheet`:
- Categorized correction types: `FACTUAL_UPDATE`, `CLARIFICATION`, `SOURCE_EXPANSION`, `TYPO_FIX`, `LEGAL_STATUS_UPDATE`.
- Severity ratings: `MINOR`, `MATERIAL`, `SUBSTANTIAL`.
- Mandatory public editorial rationale and timestamped provenance.

Eliminates silent redactions and fulfills `KEFE-GOV-001` documentation integrity standards.

## Verification & Boundary

- Contract: `docs/contracts/case-correction-history.v1.json` (PASS);
- ADR: `docs/adr/0171-case-correction-and-version-history-engine.md` (PASS);
- Backend correction service & log retrieval tests: `services/api/tests/test_correction_history.py` (PASS);
- Mobile presentation sheet & domain model tests: `apps/mobile/test/correction_history_test.dart` (PASS);
- Append-only immutable log invariant: PASS.

## Lifecycle

CAP-072 remains `ROADMAP_ACCEPTED` pending Admin Studio correction authoring dispatch integration.
