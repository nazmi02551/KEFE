# ADR-0159: Case Search and Topic Filter Engine (CAP-078/CAP-095)

## Status

ACCEPTED

## Context

As the catalog of civic, legal, and ethical cases expands, citizens must be able to discover dilemmas relevant to their immediate concerns without algorithmic polarization or engagement-maximizing feed bubbles.

## Decision

1. **User-Controlled Deterministic Search**:
   - Multi-criteria filtering by topic tag (`tags`), public domain (`domain`: e.g. `MUNICIPAL`, `HEALTHCARE`, `TECH_ETHICS`, `ENVIRONMENT`), and case activity status (`ACTIVE`, `ARCHIVED`, `SIGNAL_QUALIFIED`).
2. **Neutral Ranking Invariant**:
   - Default search sort is strictly deterministic (chronological or alphabetically balanced) with zero personalized behavioral tracking, engagement boosting, or rage-bait optimization.
3. **Keyword Stemming & Prefix Matching**:
   - Substring and tokenized prefix search across Case title, question summary, and governed domain tags.

## Consequences

- Direct user agency over content discovery.
- Strict non-partisan neutrality in search ordering.
