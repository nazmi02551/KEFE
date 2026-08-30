# Privacy-safe mobile export summary — 2026-08-30

Status: IMPLEMENTATION CANDIDATE / EXACT-HEAD CI PENDING / NO CAPABILITY
PROMOTION

Issue: #397  
Capability: CAP-085 (`ROADMAP_ACCEPTED`)  
Stack base: PR #396 exact-green head
`6758c8ae9396c62bb58e8eb0223e665a35cf6779`

ADR: ADR-0143  
Contract: `docs/contracts/privacy-safe-mobile-export-summary.v1.json`

## User-visible outcome

After a successful privacy export, the mobile confirmation can show how many
records and non-empty data groups the server included. The complete JSON is
still copied to the clipboard, and the existing notice continues to explain
that security tokens and other users' data are excluded.

## Fail-closed boundary

The summary accepts only a self-consistent `privacy-export.v2` manifest. A
legacy, absent or malformed manifest does not cause the client to inspect or
recount `product_data`; the existing generic copied confirmation remains the
fallback. Product Preview keeps its sample-only export response and therefore
does not claim a production summary.

The UI never renders internal dataset names, actor identity, digest, timestamp,
retention details or raw product data. API, OpenAPI, persistence, credentials
and deletion behavior are unchanged.

## Local evidence

- API Ruff: PASS;
- API contract sync: PASS;
- production API runtime contract: PASS;
- complete API test suite: PASS;
- JSON contract parse and repository diff checks: PASS.

Flutter format, analyzer, focused widget coverage and the complete mobile
regression suite remain exact-head CI evidence. API CI, Mobile CI, MVP Beta
Gates and Global Readiness must pass on one PR head before this candidate is
called PASS.

## Lifecycle

CAP-085 remains `ROADMAP_ACCEPTED`. This candidate does not update
`docs/status/CURRENT.md`; human review, legal review and capability governance
remain separate gates.
