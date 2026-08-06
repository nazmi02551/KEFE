# F4 Operational Readiness Evidence — 2026-08-06

## Scope

- Foundation wave: F4
- Supporting capability: CAP-123
- Exit criterion: `OBSERVABILITY_SLO_AND_ROLLBACK_EVIDENCE_EXPLICIT`
- Contract: `docs/contracts/operational-readiness-evidence.v1.json`
- ADR: ADR-0119

## Current conclusion

KEFE has source- and CI-validated operational foundations, but production operational readiness is not verified.

| Evidence item | Current state | What is actually proven |
| --- | --- | --- |
| Admin Operational Reports | `CI_VALIDATED` | Aggregate-only secured snapshot behavior, memory/PostgreSQL continuity and exact interface gates. |
| OTP delivery health | `CI_VALIDATED` | Provider-neutral final outcomes, bounded aggregate windows, privacy-safe persistence and deterministic signal policy. |
| OTP alert candidates | `CI_VALIDATED` | Durable aggregate candidates, escalation, acknowledgement and retention behavior. |
| Production deployment | `DEPLOYMENT_UNCONFIGURED` | No approved externally verified production surface exists. |
| Deployed telemetry/SLO query | `TELEMETRY_UNVERIFIED` | No production telemetry query, objective window or result provenance exists. |
| External paging | `PAGING_UNVERIFIED` | No pager destination or delivery receipt exists. |
| Incident-response execution | `OPERATOR_DRILL_PENDING` | No incident timeline and operator attestation exists. |
| Rollback execution | `OPERATOR_DRILL_PENDING` | No rollback execution record and operator attestation exists. |
| CAP-123 portfolio status | `PORTFOLIO_STATUS_STALE` | The portfolio still says `ROADMAP_ACCEPTED` although partial runtime and CI evidence exists. |

**No deployed telemetry or SLO result is verified.**

**No external paging delivery is verified.**

**No incident or rollback execution is verified.**

## Executable evidence

`services/api/tools/check_operational_readiness_evidence.py` verifies:

- the exact F4 exit-criterion and CAP-123 bindings;
- the complete status and evidence catalogs;
- that every source path exists and every item declares its next proof;
- that source/unit/CI evidence cannot produce `EXTERNALLY_VERIFIED`;
- the current Admin Operational Reports, OTP health and OTP alert foundations;
- the Admin snapshot’s explicit deployed-observability and SLO non-claims;
- the surface inventory’s absence of externally verified production reachability;
- the exact evidence requirements for deployed SLO, paging, incident and rollback claims;
- the CAP-123 `ROADMAP_ACCEPTED` portfolio/runtime mismatch;
- that F4 remains `PENDING`.

Dedicated CI reruns both parent OTP contracts and targeted memory/PostgreSQL operational tests. It includes an explicit `No deployed telemetry, pager, incident or rollback proof` step so a successful workflow cannot be interpreted as production execution.

## Exit-criterion interpretation

This slice satisfies the **explicit evidence-boundary** portion of `OBSERVABILITY_SLO_AND_ROLLBACK_EVIDENCE_EXPLICIT`:

- current engineering foundations are named and executable;
- every missing external or human proof is named;
- false equivalences are rejected by CI;
- F4 remains pending until the required external evidence is actually produced.

## Remaining external or human gates

1. approved production deployment identity and reachability;
2. timestamped deployed telemetry query with objective, window and provenance;
3. external pager destination and delivery receipt;
4. incident timeline plus operator attestation;
5. rollback execution record plus operator attestation;
6. separate governance reconciliation of CAP-123 after the stacked line is integrated.

## Non-claims

- Aggregate application reads are not a production observability backend.
- Threshold-driven signals are not SLO attainment.
- Alert candidates are not delivered pages.
- Acknowledgement is not remediation or incident closure.
- Documentation is not an operator-executed drill.
- CI success is not production readiness.
