# ADR-0143 — Privacy-safe mobile export summary

Status: CANDIDATE  
Date: 2026-08-30  
Issue: #397  
Capability: CAP-085  
Parent: PR #396 exact-green head `6758c8ae9396c62bb58e8eb0223e665a35cf6779`

## Context

The authenticated privacy API already returns a deterministic
`privacy-export.v2` document with a server-calculated manifest. The mobile
privacy screen copies the complete machine-readable JSON to the clipboard,
but the confirmation only says that the copy is ready. A user cannot see even
a bounded aggregate description of what was prepared without leaving KEFE and
inspecting the raw JSON.

## Decision

1. The mobile client may show a compact export summary only when the response
   is an internally consistent `privacy-export.v2` document.
2. The summary is derived only from `manifest.total_records`,
   `manifest.dataset_counts` and `manifest.empty_datasets`.
3. The visible summary contains the total record count and the number of data
   groups that contain at least one record.
4. Internal dataset keys, actor ID/kind, generation timestamp, digest,
   retention details and `product_data` are never rendered in the summary.
5. The complete response is still copied as indented JSON. The summary does
   not replace or alter the machine-readable export.
6. A missing, legacy or malformed manifest fails closed to the existing generic
   copied confirmation. The client does not recount `product_data` or invent a
   partial summary.
7. Product Preview keeps its sample-only repository and generic confirmation;
   it does not pretend to provide the production v2 manifest.
8. Deletion, credentials, API, OpenAPI, persistence and retention behavior are
   unchanged.

## Manifest acceptance

The client accepts a summary only when:

- `schema_version` is exactly `privacy-export.v2`;
- `dataset_counts` is a string-keyed map of non-negative integers;
- `total_records` is a non-negative integer equal to the sum of all dataset
  counts;
- `empty_datasets` is a unique string list that exactly identifies the
  zero-count dataset keys.

Any other shape is treated as unavailable summary metadata. Export copying
still succeeds because the API response itself remains the source artifact.

## Presentation and accessibility

- Turkish and English use the same two aggregate facts.
- Stable widget keys identify the summary, record count and non-empty group
  count for accessibility and regression evidence.
- The clipboard/security exclusion note remains visible in every successful
  export dialog.
- Compact phones, light/dark themes and enlarged text remain supported.

## Security and methodology boundary

This summary is a presentation of server-provided cardinalities. It is not an
analytics result, behavior score, completeness claim, legal certification,
ranking, recommendation, Signal, Impact or personal inference. It never
exposes another actor's data or reusable credentials.

## Verification

The executable contract
`docs/contracts/privacy-safe-mobile-export-summary.v1.json`, its repository
guard, pure parser tests, Turkish/English widget tests and the full mobile
regression suite must pass. API CI, Mobile CI, MVP Beta Gates and Global
Readiness must all complete on the same exact PR head before this candidate is
called PASS.

## Lifecycle

This implementation candidate does not promote CAP-085 and does not update
`docs/status/CURRENT.md`. Human review, legal review and capability governance
remain separate gates.
