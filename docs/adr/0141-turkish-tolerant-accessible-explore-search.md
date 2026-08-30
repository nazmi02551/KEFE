# ADR-0141 — Turkish-tolerant accessible Explore search

Status: IMPLEMENTATION CANDIDATE  
Date: 2026-08-30  
Issue: #393  
Capability: CAP-078  
Parent: PR #392 / `362110fa8ae34fd840b42115d00a3273f9d6b29b`

## Context

Explore already filters the currently fetched Case catalog by a literal
lowercase title/summary substring, exact domain and device-local saved state.
The literal comparison makes common Turkish ASCII input fail: for example,
`egitim` does not match `Eğitim`, and `kamusal yasam` cannot match the localized
domain label `Kamusal yaşam`. Result changes are visible but are not announced
through a dedicated screen-reader live region.

## Decision

Keep search on-device and deterministic. Normalize the query and candidate
fields with one bounded character mapping: dotted/dotless Turkish I maps to
`i`, and `ç/ğ/ö/ş/ü` map to `c/g/o/s/u`, case-insensitively. Combining dot
U+0307 is removed and whitespace is trimmed and collapsed.

Split the normalized query on spaces. Every non-empty token must occur in the
normalized union of the Case title, summary or current localized domain label.
The existing exact domain and saved-only filters remain conjunctive. Matching
preserves the canonical catalog order; no score or re-ranking is introduced.

Expose the current localized result count as visible text and a semantic live
region, including zero results. The query and filters remain ephemeral and are
cleared with the existing explicit action.

## Boundaries

This is not fuzzy search, stemming, synonym expansion, recommendation,
personalization, popularity, trend detection or behavioral profiling. It adds
no remote query, search history, analytics event, persistence, API/OpenAPI
field or migration. Product Preview and Production use the same presentation
logic over their independently composed repositories; Preview data never
becomes a Production fallback.

CAP-078 receives implementation evidence only and is not lifecycle-promoted.
Turkish/English, light/dark, compact/enlarged text, semantics and Reduce Motion
remain continuous gates.

## Evidence

The executable contract and Flutter tests bind the exact normalization map,
all-token semantics, localized-domain inclusion, stable order, filter
conjunction, result-status live region and explicit non-claims. API CI, Mobile
CI, MVP Beta Gates and Global Readiness must pass on one exact published SHA
before this slice is a verified checkpoint.
