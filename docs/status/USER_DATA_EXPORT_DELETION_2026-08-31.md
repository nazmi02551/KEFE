# User data export and cryptographic erasure lifecycle — 2026-08-31

Status: IMPLEMENTATION CANDIDATE / EXACT-HEAD CI PENDING / NO CAPABILITY PROMOTION

Issue: #408  
Capability: CAP-085 (`ROADMAP_ACCEPTED`)  
Stack base: `feature/insufficient-info-response` (`e665ec9b`)

ADR: ADR-0151  
Contract: `docs/contracts/user-data-export-and-deletion.v1.json`

## User-visible outcome

Users can perform full self-service data export and irreversible deletion directly from Settings:
1. **JSON Export**: Downloads/copies complete personal decision history, reasons, and bookmarks with SHA-256 data verification.
2. **Permanent Deletion**: Cryptographically purges all private reasons and actor identifiers, preserving aggregate statistical anonymity while issuing an official deletion receipt.

## Verification & Boundary

- Contract: `docs/contracts/user-data-export-and-deletion.v1.json` (PASS);
- ADR: `docs/adr/0151-user-data-export-and-deletion-lifecycle.md` (PASS);
- Backend privacy service & router endpoints (`/v1/me/privacy-export`, `/v1/me/privacy-delete`): PASS;
- Mobile privacy controller & export summary parser: PASS;
- Unit & integration tests: `apps/mobile/test/user_data_export_deletion_test.dart` (PASS).

## Lifecycle

CAP-085 remains `ROADMAP_ACCEPTED` pending automated cloud export download link infrastructure.
