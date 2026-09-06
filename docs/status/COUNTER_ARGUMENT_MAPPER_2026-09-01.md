# Counter-argument and refutation mapper — 2026-09-01

Status: IMPLEMENTATION CANDIDATE / EXACT-HEAD CI PENDING / NO CAPABILITY PROMOTION

Issue: #438  
Capability: CAP-043 (`ROADMAP_ACCEPTED`)  
Stack base: `feature/insufficient-info-response` (`e665ec9b`)

ADR: ADR-0181  
Contract: `docs/contracts/counter-argument-mapper.v1.json`

## User-visible outcome

Users can explore explicit dialectical pairings and refutations via `CounterArgumentCard`:
- Refutation taxonomy: `DIRECT_EMPIRICAL_REBUTTAL`, `LOGICAL_INVALIDATION`, `VALUE_HIERARCHY_CHALLENGE`, `BOUNDARY_QUALIFICATION`.
- Quantified refutation strength ($[0.0, 1.0]$) and concrete rebuttal thesis.
- Elevates civic deliberation beyond uncoordinated monologues into coherent debate graphs.

## Verification & Boundary

- Contract: `docs/contracts/counter-argument-mapper.v1.json` (PASS);
- ADR: `docs/adr/0181-counter-argument-and-refutation-mapper.md` (PASS);
- Backend refutation service & graph pairing tests: `services/api/tests/test_counter_argument.py` (PASS);
- Mobile presentation card & domain model tests: `apps/mobile/test/counter_argument_test.dart` (PASS);
- Dialectical graph pairing invariant: PASS.

## Lifecycle

CAP-043 remains `ROADMAP_ACCEPTED` pending perspective graph deliberation visualizer integration.
