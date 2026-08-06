# ADR-0119 — Operational Readiness Evidence Boundary

- **Status:** Accepted
- **Date:** 2026-08-06
- **Foundation wave:** F4
- **Supporting capability:** CAP-123
- **Exit criterion:** `OBSERVABILITY_SLO_AND_ROLLBACK_EVIDENCE_EXPLICIT`

## Context

KEFE already contains meaningful operational foundations:

- a privacy-safe aggregate Admin Operational Reports snapshot;
- durable OTP delivery-health observations with bounded windows and thresholds;
- durable OTP alert candidates with acknowledgement and escalation behavior;
- memory, PostgreSQL and CI evidence for those boundaries.

These foundations are not equivalent to production operational readiness. Repository code and CI can prove deterministic behavior, persistence, privacy and interface stability. They cannot prove that a production deployment exists, telemetry is complete, an SLO query ran against deployed data, a pager delivered a notification, an operator handled an incident or a rollback was executed.

The capability portfolio also still records CAP-123 as `ROADMAP_ACCEPTED`, while the repository contains partial runtime and CI evidence. Silently treating either side as authoritative would violate the foundation rule that capability status must match evidence.

## Decision

KEFE maintains a machine-readable operational-readiness evidence boundary at `docs/contracts/operational-readiness-evidence.v1.json`.

Every readiness item records:

1. a stable identity;
2. one bounded current status;
3. whether production verification exists;
4. the available evidence kinds and repository sources;
5. the next proof required to advance.

The accepted statuses are:

- `CI_VALIDATED`: source, tests and CI validate an engineering boundary;
- `DEPLOYMENT_UNCONFIGURED`: no approved production deployment evidence exists;
- `TELEMETRY_UNVERIFIED`: deployed telemetry query and provenance are absent;
- `PAGING_UNVERIFIED`: no external page-delivery receipt exists;
- `OPERATOR_DRILL_PENDING`: no operator-executed incident or rollback record exists;
- `PORTFOLIO_STATUS_STALE`: capability metadata does not match repository evidence;
- `EXTERNALLY_VERIFIED`: the required external evidence set is present and reviewed.

Production verification is evidence-type specific:

- SLO evidence requires a timestamped `DEPLOYED_TELEMETRY_QUERY` with objective, window and provenance;
- paging evidence requires an `ALERT_DELIVERY_RECEIPT`;
- incident-response evidence requires both an `INCIDENT_TIMELINE` and `HUMAN_OPERATOR_ATTESTATION`;
- rollback evidence requires both a `ROLLBACK_EXECUTION_RECORD` and `HUMAN_OPERATOR_ATTESTATION`.

Source definitions, unit tests and CI workflows cannot substitute for those evidence kinds. A report snapshot is not an SLO result. An internal alert candidate is not proof that a pager delivered anything. An acknowledgement is not remediation or incident closure. A runbook or ADR is not evidence that an operator executed a drill.

The CAP-123 mismatch is recorded but not repaired in this slice. Capability-portfolio promotion must occur in a separate governance change after the stacked runtime line is integrated and its exact-head evidence is accepted.

## Consequences

- F4 gains an executable and honest interpretation of `OBSERVABILITY_SLO_AND_ROLLBACK_EVIDENCE_EXPLICIT`.
- Existing operational foundations remain valuable without being promoted into production claims.
- Every missing external or human gate has a named proof requirement.
- Future deployment work can advance one evidence item without falsely advancing unrelated items.
- Public API, database schema and runtime behavior remain unchanged.

## Explicit non-claims

This decision does not prove:

- a production deployment;
- a deployed telemetry backend or complete production instrumentation;
- SLO attainment, error-budget health, availability or latency;
- external pager delivery or destination configuration;
- incident detection effectiveness, diagnosis, remediation or closure;
- operator response effectiveness;
- a rollback execution, recovery time or recovery point objective;
- production readiness of F4;
- CAP-123 lifecycle promotion.

CI validates engineering contracts. It does not operate the production system.
