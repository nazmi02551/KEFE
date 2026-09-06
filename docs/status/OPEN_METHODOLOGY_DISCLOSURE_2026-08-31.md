# Open methodology disclosure per result / Signal — 2026-08-31

Status: IMPLEMENTATION CANDIDATE / EXACT-HEAD CI PENDING / NO CAPABILITY PROMOTION

Issue: #405  
Capability: CAP-074 (`ROADMAP_ACCEPTED`)  
Stack base: `feature/insufficient-info-response` (`e665ec9b`)

ADR: ADR-0148  
Contract: `docs/contracts/open-methodology-disclosure.v1.json`

## User-visible outcome

Users can now tap directly on the methodology indicator on any collective result card to open a governed `OpenMethodologySheet`. 

The sheet discloses the statistical engine version, audited sample size, confidence tier, and the three core deliberation safeguards:
1. **Commit First**: Blind voting isolation prior to reveal.
2. **Anti-Sybil**: Filtering of coordinated and bot traffic.
3. **No Profiling**: Explicit declaration that no psychometric or ideological inferences are drawn.

## Verification & Boundary

- Contract: `docs/contracts/open-methodology-disclosure.v1.json` (PASS);
- ADR: `docs/adr/0148-open-methodology-disclosure.md` (PASS);
- Mobile bottom sheet component: `open_methodology_sheet.dart` (PASS);
- Interactive trigger integration: `reveal_result_card.dart` (PASS);
- Turkish & English localization catalogs: PASS;
- Unit tests: `apps/mobile/test/open_methodology_test.dart` (PASS).

## Lifecycle

CAP-074 remains `ROADMAP_ACCEPTED` pending Signal hub surface rollouts.
