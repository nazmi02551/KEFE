# ADR-0218: Real-Time Service Health & Incident Transparency (CAP-088)

## Status

ACCEPTED

## Context

Trust in democratic deliberation infrastructure requires unconditional operational transparency regarding API latency, service uptime, incident status, and cryptographic verification latency. Under `KEFE-PB-001`, `KEFE-ETG-001`, and `KEFE-ENG-001`, KEFE provides a public, real-time Service Health & Incident Transparency monitor.

## Decision

1. **Service Health Status Taxonomy**:
   - `OPERATIONAL_OPTIMAL`: All subsystems nominal ($\text{p99} \le 120\text{ ms}$).
   - `DEGRADED_PERFORMANCE`: Increased latency without data loss.
   - `INCIDENT_ACTIVE`: Active mitigation underway with real-time public post-mortem feed.
2. **Availability Invariant**:
   - Status endpoint operates on separate resilient infra to ensure status is readable during core API disruptions.

## Consequences

- Fosters total institutional trustworthiness.
- Prevents ambiguity during high-traffic civic deliberation spikes.
