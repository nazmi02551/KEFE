# ADR-0140 — Bounded Community Reason pattern distribution

Status: IMPLEMENTATION CANDIDATE  
Date: 2026-08-30  
Issue: #391  
Capability: CAP-032  
Parent: PR #390 / `448379b3f6521e821192d6dbf322012b5a41493b`

## Context

KEFE already exposes moderated, post-Commit Community Reasons and a bounded set
of server-derived reason-tag counts. The response also exposes `sample_size`,
but the in-memory and PostgreSQL repositories currently count tags only inside
the latest-item response window while `sample_size` counts every publicly
readable contribution for the CaseVersion. Those two values therefore describe
different populations once the item window is full.

The phone experience renders the existing counts as small chips. It does not
explain the denominator, the non-exclusive multi-tag model or how much of the
published contribution set each pattern represents. Presenting percentages or
an exclusive pie from the current values would be methodologically false.

## Decision

`tag_pattern_counts` and `sample_size` describe the same complete set of
currently publicly readable Community Reasons for the exact immutable
CaseVersion. The returned `items` list remains an independently bounded,
latest-first reading window.

Each contribution counts at most once for each distinct raw tag code. A
contribution may count toward several tags, so tag rows are non-exclusive and
their counts may sum to more than `sample_size`. The API preserves raw codes;
the phone localizes only their presentation labels.

The phone presents a deterministic descriptive summary after Commit:

- pattern rows sort by count descending and raw tag code ascending;
- every row exposes the exact `count / sample_size` values in text and
  accessibility semantics;
- a bounded determinate bar visualizes that single-tag ratio;
- localized copy states that one contribution may contain several tags and
  that rows do not add up to 100%;
- no animation is required for comprehension.

Malformed count/denominator responses fail closed in the production HTTP
client. Counts must be positive integers no greater than `sample_size`; a zero
sample must have no tag counts.

## Methodology and product boundary

The summary is descriptive only. Count or visual order is not popularity,
truth, importance, quality, representativeness, agreement, recommendation,
Signal eligibility or Impact. It does not expose author identity, demographics
or inferred traits and does not perform ideology, psychometric, bias or causal
inference.

Existing moderation eligibility remains authoritative: only
`NOT_REQUIRED` and `ALLOWED` contributions are counted. Pending or blocked
contributions remain absent. Reactions remain separate and do not affect the
pattern summary.

## User experience

The shared Production/Product Preview Community Reasons section owns the
summary. It supports Turkish and English, light and dark themes, compact phones,
enlarged text, semantic reading order and Reduce Motion. The existing feature
gate, publish, reaction, report and moderation receipt flows remain unchanged.

CAP-032 remains `IMPLEMENTED_PARTIAL`. Trend history, demographic breakdown,
ranking, recommendation, author identity, methodology-qualified Signal/Impact
and human/editorial acceptance remain separate work.

## Persistence and compatibility

No database migration or response-shape change is required. PostgreSQL adds a
separate aggregate query over the complete readable population. In-memory
composition applies the same rule. Existing clients continue to receive the
same fields, now with internally consistent semantics.

## Evidence

The executable contract and tests bind population parity, item-window
independence, per-contribution tag de-duplication, moderation filtering,
deterministic ordering, strict transport validation, localization,
accessibility and compact/enlarged presentation. API CI, Mobile CI, MVP Beta
Gates and Global Readiness must pass on one exact candidate SHA before this
slice is a verified checkpoint.
