# Context drift alerting engine — 2026-08-31

Status: IMPLEMENTATION CANDIDATE / EXACT-HEAD CI PENDING / NO CAPABILITY PROMOTION

Issue: #413  
Capability: CAP-076 (`ROADMAP_ACCEPTED`)  
Stack base: `feature/insufficient-info-response` (`e665ec9b`)

ADR: ADR-0156  
Contract: `docs/contracts/context-drift-alerting.v1.json`

## User-visible outcome

When a real-world legal reform, scientific factual update, or assumption change occurs after a Case is published:
- Users receive a non-coercive, audited `ContextDriftNotice` prior to decision commit.
- Historical snapshots retain their original validity while new deliberations proceed with clear awareness.

## Verification & Boundary

- Contract: `docs/contracts/context-drift-alerting.v1.json` (PASS);
- ADR: `docs/adr/0156-context-drift-alerting-engine.md` (PASS);
- Backend service and retrieval tests: `services/api/tests/test_context_drift.py` (PASS);
- Historical snapshot preservation invariant: PASS.

## Lifecycle

CAP-076 remains `ROADMAP_ACCEPTED` pending editorial drift publishing tooling.
