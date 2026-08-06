# ADR-0121: CAP-123 governance reconciliation

- Status: Accepted for evidence reconciliation only
- Date: 2026-08-07
- Foundation wave: F4
- Capability: CAP-123 — Admin operational/trust/editorial reports
- Issue: #339
- Parent stack: PR #338 and its ancestors

## Context

The canonical capability portfolio still records CAP-123 as
`ROADMAP_ACCEPTED`. The stacked F4 implementation line now contains meaningful
repository and CI evidence for aggregate admin operational reporting, OTP
provider and delivery-health observations, durable alert candidates,
operational-readiness evidence boundaries, and operator-drill evidence
acceptance.

That implementation evidence creates a real governance mismatch, but it does
not authorize the delivery mirror to rewrite the product lifecycle. The
Product Bible remains the owning product source, while the capability portfolio
is a governed mirror of that decision.

Production deployment, external reachability, deployed telemetry and SLO
results, external pager delivery receipts, and human incident-response and
rollback attestations are still absent. Therefore the evidence cannot support
`IMPLEMENTED_VERIFIED`.

## Decision

**Evidence reconciliation is not lifecycle promotion.**

This change catalogs the repository/runtime and CI evidence for CAP-123 while
requiring the canonical portfolio row to remain `ROADMAP_ACCEPTED`.

**The repository mirror cannot create a Product Bible decision.** An explicit
owning-document and documentation-governance decision is required before the
portfolio lifecycle can change.

**IMPLEMENTED_PARTIAL is a candidate state, not an automatic transition.** It
is eligible for governance review only after the stacked implementation line
is integrated and exact-head CI evidence is retained. This ADR does not perform
that transition.

`IMPLEMENTED_VERIFIED` remains blocked until all required production, external,
behavioral, and human-operator evidence exists and the owning document approves
the lifecycle decision.

## Evidence classes

### Repository/runtime evidence

The repository contains versioned contracts, runtime services, HTTP and
PostgreSQL tests, and dedicated workflows for aggregate admin operational
reports and delivery observability. This proves implemented repository
behavior within the tested boundaries.

### CI protocol evidence

Operational-readiness and operator-drill validators make missing evidence
explicit and prevent templates or CI simulations from becoming production or
human proof.

### Evidence not present

The repository does not currently prove:

- an approved production deployment identity;
- externally observed production reachability;
- a deployed telemetry query with SLO or error-budget results;
- an external pager delivery receipt;
- a human-attested incident-response exercise;
- a human-attested rollback execution;
- production RTO or RPO attainment.

## Consequences

- CAP-123 remains `ROADMAP_ACCEPTED` in the canonical portfolio.
- Repository and CI evidence becomes discoverable and machine-verifiable.
- Silent or incidental lifecycle promotion fails CI.
- `IMPLEMENTED_PARTIAL` can be proposed later through the owning governance
  process; it is not granted here.
- `IMPLEMENTED_VERIFIED` remains unavailable while production and human proof
  is incomplete.
- F4 remains pending.

## Non-goals

This ADR does not change runtime behavior, public APIs, OpenAPI, migrations,
database schemas, production deployment configuration, product semantics, or
the CAP-123 portfolio lifecycle.
