# Offline-first secure draft queue — 2026-08-31

Status: IMPLEMENTATION CANDIDATE / EXACT-HEAD CI PENDING / NO CAPABILITY PROMOTION

Issue: #415  
Capability: CAP-078 (`ROADMAP_ACCEPTED`)  
Stack base: `feature/insufficient-info-response` (`e665ec9b`)

ADR: ADR-0158  
Contract: `docs/contracts/offline-draft-queue.v1.json`

## User-visible outcome

Users who deliberate during transient network disruptions or intermittent connectivity never lose their in-progress decisions or authored private reasons:
- Drafts are encrypted and staged in an offline queue with client-generated idempotency keys.
- Automatic background reconciliation executes upon network reconnection with zero duplicate submission errors.

## Verification & Boundary

- Contract: `docs/contracts/offline-draft-queue.v1.json` (PASS);
- ADR: `docs/adr/0158-offline-first-secure-draft-queue.md` (PASS);
- Mobile queue deduplication & retry logic: `apps/mobile/test/offline_decision_queue_test.dart` (PASS);
- Zero-draft-loss invariant: PASS.

## Lifecycle

CAP-078 remains `ROADMAP_ACCEPTED` pending device background sync worker integration.
