# Bridge arguments and shared ground engine — 2026-08-31

Status: IMPLEMENTATION CANDIDATE / EXACT-HEAD CI PENDING / NO CAPABILITY PROMOTION

Issue: #418  
Capability: CAP-034 (`ROADMAP_ACCEPTED`)  
Stack base: `feature/insufficient-info-response` (`e665ec9b`)

ADR: ADR-0161  
Contract: `docs/contracts/bridge-arguments.v1.json`

## User-visible outcome

When sharp polarization exists, users see verified `BridgeArgumentCard` components that highlight:
- Core synthesis theses that connect opposing voter factions ($\ge 35\%$ cross-group resonance).
- Tagged connecting values that both sides hold in common.
- Privacy-guarded sample size indicators ($n \ge 30$).

## Verification & Boundary

- Contract: `docs/contracts/bridge-arguments.v1.json` (PASS);
- ADR: `docs/adr/0161-bridge-arguments-and-shared-ground-engine.md` (PASS);
- Backend bridge argument service & validation tests: `services/api/tests/test_bridge_arguments.py` (PASS);
- Mobile presentation card & domain model tests: `apps/mobile/test/bridge_arguments_test.dart` (PASS);
- Non-fabrication & statistical threshold invariants: PASS.

## Lifecycle

CAP-034 remains `ROADMAP_ACCEPTED` pending automated cross-cluster semantic resonance pipeline integration.
