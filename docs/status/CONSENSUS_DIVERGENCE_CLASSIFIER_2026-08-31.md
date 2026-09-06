# Consensus and divergence classification engine — 2026-08-31

Status: IMPLEMENTATION CANDIDATE / EXACT-HEAD CI PENDING / NO CAPABILITY PROMOTION

Issue: #419  
Capability: CAP-039 (`ROADMAP_ACCEPTED`)  
Stack base: `feature/insufficient-info-response` (`e665ec9b`)

ADR: ADR-0162  
Contract: `docs/contracts/consensus-divergence-classification.v1.json`

## User-visible outcome

The KEFE decision runtime automatically categorizes collective outcomes into four objective, non-normative structural typologies:
- `BROAD_CONSENSUS`: Overwhelming agreement ($\ge 70\%$).
- `BIPOLAR_DIVERGENCE`: Tight two-way polarization (margin $\le 15\%$, combined $\ge 80\%$).
- `FRAGMENTED_PLURALITY`: Distributed multi-way opinion without dominant consensus.
- `LEANING_MAJORITY`: Moderate majority support ($55\% - 70\%$).

## Verification & Boundary

- Contract: `docs/contracts/consensus-divergence-classification.v1.json` (PASS);
- ADR: `docs/adr/0162-consensus-and-divergence-classification-engine.md` (PASS);
- Backend classifier tests: `services/api/tests/test_divergence_classifier.py` (PASS);
- Descriptive non-normative invariant: PASS.

## Lifecycle

CAP-039 remains `ROADMAP_ACCEPTED` pending collective reveal screen visual badge integration.
