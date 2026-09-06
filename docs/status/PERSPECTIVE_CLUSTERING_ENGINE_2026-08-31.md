# Multi-party perspective clustering engine — 2026-08-31

Status: IMPLEMENTATION CANDIDATE / EXACT-HEAD CI PENDING / NO CAPABILITY PROMOTION

Issue: #417  
Capability: CAP-033 (`ROADMAP_ACCEPTED`)  
Stack base: `feature/insufficient-info-response` (`e665ec9b`)

ADR: ADR-0160  
Contract: `docs/contracts/perspective-clustering.v1.json`

## User-visible outcome

Users can explore public reason spaces through structured semantic argument archetypes:
- `NEAR_CONSENSUS`: Dominant mainstream reasoning.
- `OPPOSING_PRINCIPLE`: Robust opposing principled minority stances.
- `BRIDGE_SYNTHESIS`: Compromise and shared-ground proposals.
- `ALTERNATIVE_PARADIGM`: Out-of-the-box reframings of the dilemma.

Presents the full spectrum of deliberation without algorithmic bias or echo-chamber reinforcement.

## Verification & Boundary

- Contract: `docs/contracts/perspective-clustering.v1.json` (PASS);
- ADR: `docs/adr/0160-multi-party-perspective-clustering-engine.md` (PASS);
- Backend clustering service tests: `services/api/tests/test_perspective_clustering.py` (PASS);
- Balanced representation invariant: PASS.

## Lifecycle

CAP-033 remains `ROADMAP_ACCEPTED` pending ML clustering batch pipeline integration.
