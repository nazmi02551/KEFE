# F4 CAP-123 Governance Reconciliation — 2026-08-07

## Checkpoint

Issue #339 records the mismatch between the canonical capability portfolio and
the repository/runtime evidence delivered by the stacked F4 line.

**CAP-123 remains `ROADMAP_ACCEPTED`.** The canonical portfolio is not edited by
this slice.

| Area | Current state | Evidence boundary | Next authorized gate |
|---|---|---|---|
| Portfolio lifecycle | `ROADMAP_ACCEPTED` | Canonical mirror unchanged | Explicit Product Bible and documentation-governance decision |
| Repository/runtime implementation | Present | Versioned contracts, runtime paths and tests | Parent stack integration and retained exact-head CI |
| CI validation | Present | Repository behavior and evidence boundaries only | Successful exact-head workflows on the integrated line |
| Candidate lifecycle | `IMPLEMENTED_PARTIAL` review candidate | Not granted by this change | Owning-document approval after integration |
| Production deployment | Unverified | No approved deployment identity | Approved production deployment and external reachability |
| Deployed telemetry/SLO | Unverified | Repository snapshots are not deployed SLO proof | Timestamped production query, objective, window and result |
| External paging | Unverified | Alert candidates are not delivery receipts | Production pager delivery receipt |
| Incident response | `OPERATOR_DRILL_PENDING` | Templates and CI simulations are not human execution | Human timeline and independent attestation |
| Rollback | `OPERATOR_DRILL_PENDING` | No approved-environment execution record | Human rollback record and independent attestation |
| Verified lifecycle | Blocked | Production, external and human proof incomplete | Complete evidence set plus owning-document decision |

## Delivered

- a versioned CAP-123 governance reconciliation contract;
- an executable validator that compares the contract, portfolio and parent F4
  evidence state;
- explicit separation of repository/CI evidence from deployed, external and
  human evidence;
- an ADR defining lifecycle authority and the candidate-state boundary;
- dedicated CI chained to the existing capability-portfolio and F4 evidence
  validators.

## Governance boundary

**No lifecycle promotion is performed.** `IMPLEMENTED_PARTIAL` is identified
only as the next eligible governance-review candidate. It is not written into
the canonical portfolio and is not represented as an approved product
lifecycle decision.

`IMPLEMENTED_VERIFIED` is prohibited while the production deployment,
reachability, deployed telemetry/SLO, pager delivery, incident-response,
rollback, behavioral-validation and owning-document gates remain incomplete.

## Product and runtime boundary

No runtime behavior, public API, OpenAPI, migration, database schema, deployment
configuration or product behavior changes in this slice.

No production readiness claim is made. **F4 remains pending.**

## Next authorized action

After PR #338 and its parent stack are integrated with successful exact-head CI,
the Product Bible/documentation-governance process may decide whether CAP-123
should move from `ROADMAP_ACCEPTED` to `IMPLEMENTED_PARTIAL`. That later change
must carry its own authority, evidence references and review record.
