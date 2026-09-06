# Signal decay and freshness engine — 2026-08-31

Status: IMPLEMENTATION CANDIDATE / EXACT-HEAD CI PENDING / NO CAPABILITY PROMOTION

Issue: #411  
Capability: CAP-075 (`ROADMAP_ACCEPTED`)  
Stack base: `feature/insufficient-info-response` (`e665ec9b`)

ADR: ADR-0154  
Contract: `docs/contracts/signal-decay-and-freshness.v1.json`

## User-visible outcome

The KEFE Signal Engine now features an exponential half-life decay model ($T_{1/2} = 30$ days) that categorizes consensus signals into four clear freshness tiers:
- `FRESH` ($\ge 0.85$): Active community deliberation.
- `STABLE` ($0.50 \le S < 0.85$): Established consensus.
- `DECAYING` ($0.20 \le S < 0.50$): Waning activity prompt.
- `ARCHIVED` ($< 0.20$): Historical record (formal signal authority revoked).

Incoming verified weighs automatically refresh the signal to active status.

## Verification & Boundary

- Contract: `docs/contracts/signal-decay-and-freshness.v1.json` (PASS);
- ADR: `docs/adr/0154-signal-decay-and-freshness-engine.md` (PASS);
- Backend calculation & half-life tests: `services/api/tests/test_signal_freshness.py` (PASS);
- Deterministic decay invariant: PASS.

## Lifecycle

CAP-075 remains `ROADMAP_ACCEPTED` pending Signal dashboard scheduler deployments.
