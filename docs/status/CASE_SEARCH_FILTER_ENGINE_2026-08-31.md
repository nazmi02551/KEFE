# Case search and topic filter engine — 2026-08-31

Status: IMPLEMENTATION CANDIDATE / EXACT-HEAD CI PENDING / NO CAPABILITY PROMOTION

Issue: #416  
Capability: CAP-078 (`ROADMAP_ACCEPTED`)  
Stack base: `feature/insufficient-info-response` (`e665ec9b`)

ADR: ADR-0159  
Contract: `docs/contracts/case-search-filter.v1.json`

## User-visible outcome

Citizens can discover deliberation cases using user-controlled search filters:
- Multi-criteria filtering by topic tags (`tags`), public sector domains (`domain`), and status (`ACTIVE`, `ARCHIVED`, `SIGNAL_QUALIFIED`).
- Substring and tokenized keyword search across titles, summaries, and tags.
- Non-polarized, deterministic chronological ranking without behavioral feed tracking or engagement algorithms.

## Verification & Boundary

- Contract: `docs/contracts/case-search-filter.v1.json` (PASS);
- ADR: `docs/adr/0159-case-search-and-topic-filter-engine.md` (PASS);
- Backend search filter service tests: `services/api/tests/test_case_search_filter.py` (PASS);
- Neutral ranking invariant: PASS.

## Lifecycle

CAP-078 remains `ROADMAP_ACCEPTED` pending client explore search bar integration.
