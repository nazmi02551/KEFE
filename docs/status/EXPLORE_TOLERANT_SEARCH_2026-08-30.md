# Explore tolerant search — 2026-08-30

Status: IMPLEMENTATION CANDIDATE / EXACT-HEAD CI PENDING / NO CAPABILITY PROMOTION

Issue: #393  
Pull request: pending  
Capability: CAP-078 (`ROADMAP_ACCEPTED`)  
Stack base: PR #392 exact-green head
`362110fa8ae34fd840b42115d00a3273f9d6b29b`

ADR: ADR-0141  
Contract: `docs/contracts/explore-tolerant-search.v1.json`

## User-visible outcome

Explore accepts common ASCII equivalents for Turkish search input, including
`egitim` for `Eğitim` and `kamusal yasam` for `Kamusal yaşam`. Multi-word
queries require every token to occur across the title, summary or localized
domain label. The current result count is visible and announced as a localized
live region.

Search remains an ephemeral filter over the already fetched catalog. It does
not reorder Cases, call a remote service, persist history, emit analytics or
create a recommendation/profile signal. Exact domain and saved-only controls
remain conjunctive and unchanged.

## Evidence boundary

Pure normalization and matching tests, Product Preview navigation tests,
localization parity and compact/enlarged presentation are required. Repository
CI must verify Flutter format, analyze, the full mobile suite, API continuity,
PostgreSQL continuity and Android compile evidence on one exact SHA.

CAP-078 is not promoted by this candidate. Fuzzy search, stemming, synonyms,
remote full-text indexing, search history, ranking, recommendation,
personalization, production SLO and human usability remain separate gates.
This candidate does not update `docs/status/CURRENT.md`.
