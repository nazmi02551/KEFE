# Cognitive fallacy and distortion detector — 2026-09-01

Status: IMPLEMENTATION CANDIDATE / EXACT-HEAD CI PENDING / NO CAPABILITY PROMOTION

Issue: #434  
Capability: CAP-042 (`ROADMAP_ACCEPTED`)  
Stack base: `feature/insufficient-info-response` (`e665ec9b`)

ADR: ADR-0177  
Contract: `docs/contracts/fallacy-distortion-detector.v1.json`

## User-visible outcome

Users receive real-time pedagogical feedback on informal cognitive fallacies via `FallacyDetectorCard`:
- Fallacy classifications: `AD_HOMINEM`, `STRAW_MAN`, `FALSE_DILEMMA`, `SLIPPERY_SLOPE`, `APPEAL_TO_EMOTION_FEAR`, `NO_FALLACY_DETECTED`.
- Deductive overall argument integrity scoring without punitive censorship.
- Fosters sound logic and epistemically healthy civic discourse.

## Verification & Boundary

- Contract: `docs/contracts/fallacy-distortion-detector.v1.json` (PASS);
- ADR: `docs/adr/0177-cognitive-fallacy-and-distortion-detector.md` (PASS);
- Backend fallacy detector & integrity deduction tests: `services/api/tests/test_fallacy_detector.py` (PASS);
- Mobile presentation card & domain model tests: `apps/mobile/test/fallacy_detector_test.dart` (PASS);
- Standard fallacy taxonomy invariant: PASS.

## Lifecycle

CAP-042 remains `ROADMAP_ACCEPTED` pending automated community reason submission classifier pipeline integration.
