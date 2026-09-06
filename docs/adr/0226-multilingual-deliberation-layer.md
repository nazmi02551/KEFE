# ADR-0226: Multilingual Universal Deliberation & Translation Layer (CAP-080)

## Status

ACCEPTED

## Context

Global and multi-ethnic civic dilemmas require cross-language deliberation where arguments written in Turkish, English, Arabic, Kurdish, or other tongues can be semantically translated without losing normative nuance or mutating raw backend values. Under `KEFE-PB-001`, `KEFE-ETG-001`, and `KEFE-ENG-001`, KEFE provides a Multilingual Universal Deliberation Layer.

## Decision

1. **Translation Fidelity Tier Taxonomy**:
   - `HIGH_FIDELITY_CERTIFIED`: Human or high-grade semantic neural translation preserved.
   - `COMMUNITY_VERIFIED`: Peer-reviewed translations across linguistic communities.
   - `MACHINE_RAW_PREVIEW`: Direct automated machine translation for immediate comprehension.
2. **Immutability Invariant**:
   - Display localization and translations must never alter underlying canonical CaseVersion identifiers or original source strings.

## Consequences

- Bridges linguistic divides across diverse citizen communities.
- Preserves dialectal nuances and normative precision.
