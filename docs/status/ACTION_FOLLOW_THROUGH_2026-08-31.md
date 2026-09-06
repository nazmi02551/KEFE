# Action proposal and milestone follow-through — 2026-08-31

Status: IMPLEMENTATION CANDIDATE / EXACT-HEAD CI PENDING / NO CAPABILITY PROMOTION

Issue: #409  
Capability: CAP-051 (`ROADMAP_ACCEPTED`)  
Stack base: `feature/insufficient-info-response` (`e665ec9b`)

ADR: ADR-0152  
Contract: `docs/contracts/action-follow-through.v1.json`

## User-visible outcome

Users can track concrete civic, legislative, and institutional actions that emerge from community consensus:
- View structured action milestones with real-time completion progress indicators (`progress_percentage` 0-100%).
- Review status states: `PROPOSED`, `IN_PROGRESS`, `VERIFIED_COMPLETE`, `STALLED`.
- Inspect official evidence summaries and external links verifying progress.

## Verification & Boundary

- Contract: `docs/contracts/action-follow-through.v1.json` (PASS);
- ADR: `docs/adr/0152-action-proposal-and-milestone-follow-through.md` (PASS);
- Backend action service & milestone models: `services/api/src/kefe_api/modules/impact/` (PASS);
- Mobile presentation card & domain models: `apps/mobile/lib/features/impact/` (PASS);
- Turkish & English localization catalogs: PASS;
- Unit tests: `services/api/tests/test_action_follow_through.py` & `apps/mobile/test/action_follow_through_test.dart` (PASS).

## Lifecycle

CAP-051 remains `ROADMAP_ACCEPTED` pending live community action proposal tooling.
