# ADR-0192: Verified Institution Response Protocol (CAP-049)

## Status

ACCEPTED

## Context

When collective signals target policy dilemmas impacting institutions (ministries, municipalities, regulators, corporations), democratic closure requires a formal, cryptographically authenticated response mechanism. Under `KEFE-MPD-001`, `KEFE-ADM-001`, and `KEFE-SEC-001`, Verified Institution Response allows authorized spokespersons to attach binding official statements.

## Decision

1. **Verification Taxonomy**:
   - `OFFICIAL_GOVERNMENT`: Verified state or ministerial authority.
   - `MUNICIPAL_LOCAL`: Local government or regional municipality.
   - `CORPORATE_ENTERPRISE`: Regulated commercial enterprise or utility provider.
   - `CIVIL_SOCIETY`: Recognized NGO or consumer advocacy federation.
2. **Protocol Invariants**:
   - Verification must use domain validation, DKIM/PGP, or cryptographic organizational credentials.
   - Responses are published alongside the original signal without overwriting community consensus.

## Consequences

- Direct two-way accountability loop between citizens and institutions.
- Tamper-proof institutional voice.
