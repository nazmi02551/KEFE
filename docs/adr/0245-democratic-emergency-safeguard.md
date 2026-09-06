# ADR-0245: Democratic Emergency & State-of-Exception Safeguard (CAP-113)

## Status

ACCEPTED

## Context

States of emergency and crisis decrees frequently lead to creeping authoritarianism and executive power overreach. Under `KEFE-PB-001`, `KEFE-ETG-001`, and `KEFE-ENG-001`, KEFE establishes a Democratic Emergency & State-of-Exception Safeguard providing cryptographic sunset tracking, fundamental human rights derogation boundaries, and parliamentary review timers.

## Decision

1. **Emergency Safeguard Status Taxonomy**:
   - `PROPORTIONATE_SUNSET_BOUNDED`: Crisis decree has strict proportionality bounds, non-derogable rights immunity, and verifiable automatic sunset timer.
   - `SUNSET_EXPIRATION_APPROACHING`: Emergency decree nearing statutory expiration date requiring legislative re-authorization.
   - `AUTHORITARIAN_CREEP_VIOLATION`: Proportionality violated or indefinite suspension of non-derogable civil rights detected.
2. **Safeguard Invariant**:
   - Emergency powers without verifiable cryptographic sunset clauses trigger maximum constitutional risk alerts.

## Consequences

- Prevents normalization of temporary emergency decrees into permanent executive rule.
- Safeguards core civil liberties during national crises.
