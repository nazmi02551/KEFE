# ADR-0142 — Consumer Context information-status guide

Status: CANDIDATE  
Date: 2026-08-30  
Issue: #395  
Capabilities: CAP-069, CAP-070  
Parent: PR #394 exact-green head `826f6efdf7cd3a07d980f95e2c53fe78b4ef99f6`

## Context

Consumer Context already renders block-level `VERIFIED`, `CLAIMED`,
`DISPUTED` and `UNKNOWN` badges and verification-neutral source references.
The labels are visible, but the screen does not explain their meaning. A user
must therefore guess whether a badge applies to the information block, its
linked source, or both. The source model also carries an optional
`publishedAt` value that the current micro-preview does not show.

## Decision

1. Both legacy and progressive Context presentations use one shared,
   collapsed-by-default information-status guide.
2. The guide explains all four canonical block statuses in Turkish and English.
3. The guide states explicitly that a block status does not independently
   verify a linked source.
4. The explanations are descriptive presentation copy. They do not create or
   change editorial methodology, evidence requirements or domain state.
5. The neutral source tile shows the existing publication date when present,
   using a deterministic calendar-date representation.
6. Publication date, publisher, source kind and URL host remain provenance
   metadata. None is rendered or interpreted as a trust score or verification
   signal.
7. No backend, OpenAPI, database, ranking, recommendation, Signal or Impact
   surface changes in this slice.

## Status copy boundary

- `VERIFIED`: the editorial record marks the information block as checked.
- `CLAIMED`: the block presents a claim and is not marked verified.
- `DISPUTED`: the available record contains disagreement about the block.
- `UNKNOWN`: the current record does not establish a status for the block.

These descriptions explain current presentation state only. They must not be
projected onto a linked source, used to rank Cases, or treated as a factual
confidence score.

## Accessibility and presentation

- the guide has stable semantics and a stable disclosure key;
- color is supplementary and never the only status carrier;
- Turkish and English copy have parity;
- compact phones, light/dark themes and enlarged text remain supported;
- the source date is omitted cleanly when the API value is absent.

## Verification

The executable contract
`docs/contracts/context-information-status-guide.v1.json`, its repository
guard, focused widget tests and the full mobile regression suite must pass.
API CI, Mobile CI, MVP Beta Gates and Global Readiness must all complete on the
same exact PR head before this candidate is called PASS.

## Lifecycle

This implementation candidate does not promote CAP-069 or CAP-070 and does not
update `docs/status/CURRENT.md`. Human review and capability governance remain
separate gates.
