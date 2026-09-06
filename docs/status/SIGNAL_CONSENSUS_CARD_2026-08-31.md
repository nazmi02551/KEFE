# Signal and consensus card composition — 2026-08-31

Status: IMPLEMENTATION CANDIDATE / EXACT-HEAD CI PENDING / NO CAPABILITY PROMOTION

Issue: #421  
Capability: CAP-016 (`ROADMAP_ACCEPTED`)  
Stack base: `feature/insufficient-info-response` (`e665ec9b`)

ADR: ADR-0164  
Contract: `docs/contracts/signal-consensus-card.v1.json`

## User-visible outcome

Users and civic observers can view mature community consensus via the `SignalConsensusCard`:
- Verified confidence tiers (`GOLD`, `SILVER`, `BRONZE`) determined by sample volume ($n \ge 100$) and consensus agreement thresholds.
- Official consensus statement and sample size badges.
- Tappable exploration into full open methodology and audited verification history.

## Verification & Boundary

- Contract: `docs/contracts/signal-consensus-card.v1.json` (PASS);
- ADR: `docs/adr/0164-signal-and-consensus-card-composition.md` (PASS);
- Backend card composer & tier assignment tests: `services/api/tests/test_signal_consensus_card.py` (PASS);
- Mobile presentation card & domain model tests: `apps/mobile/test/signal_consensus_card_test.dart` (PASS);
- Non-coercive disclaimer invariant: PASS.

## Lifecycle

CAP-016 remains `ROADMAP_ACCEPTED` pending Signal feed consumer surface integration.
