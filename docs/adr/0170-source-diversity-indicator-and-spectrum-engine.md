# ADR-0170: Source Diversity Indicator and Spectrum Engine (CAP-071)

## Status

ACCEPTED

## Context

In accordance with `KEFE-TIM-001` (Trust & Integrity Methodology Standard) and `KEFE-ETG-001` (Editorial Transformation Guide), a case must not derive its context or perspective evidence from a single editorial or political monoculture. Citizens must be able to verify at a glance that a dilemma is supported by a pluralistic spectrum of verified sources.

## Decision

1. **Source Plurality Taxonomy**:
   - `ACADEMIC_SCIENTIFIC`: Peer-reviewed research, academic journals.
   - `OFFICIAL_GOVERNMENT`: Statistical institutes, gazettes, public records.
   - `CIVIC_INDEPENDENT`: Independent NGOs, civil society organizations.
   - `MAINSTREAM_JOURNALISM`: Verified press outlets across differing editorial philosophies.
   - `TECHNICAL_INDUSTRY`: Engineering, operational, and specialized domain reports.
2. **Diversity Score & Level**:
   - Computes entropy/dispersion index across categories:
     - `HIGH_DIVERSITY` (3+ categories, balanced distribution).
     - `BALANCED_DIVERSITY` (2-3 categories).
     - `LIMITED_DIVERSITY` (Single dominant source category).

## Consequences

- Prevents echo chamber capture and editorial bias.
- Meets the trust and integrity standards outlined in the KEFE Product Bible.
