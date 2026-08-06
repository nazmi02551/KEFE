# F4 Operator Drill Evidence Protocol — 2026-08-06

## Checkpoint

Issue #336 introduces an executable acceptance protocol for the
`INCIDENT_TIMELINE`, `ROLLBACK_EXECUTION_RECORD`, and
`HUMAN_OPERATOR_ATTESTATION` evidence kinds required by PR #335.

| Area | Current state | Repository evidence | What is still required |
|---|---|---|---|
| Incident-response template | `TEMPLATE_ONLY` | Versioned JSON template | Human execution in an approved environment |
| Incident-response CI fixture | `CI_SIMULATED` | Synthetic ordered timeline | Human operator and independent approver attestations |
| Incident-response execution | `OPERATOR_DRILL_PENDING` | No accepted human record | Privacy-safe timeline, artifacts and sign-off |
| Rollback template | `TEMPLATE_ONLY` | Versioned JSON template | Human execution in an approved environment |
| Rollback CI fixture | `CI_SIMULATED` | Synthetic ordered timeline | Human operator and independent approver attestations |
| Rollback execution | `OPERATOR_DRILL_PENDING` | No accepted human record | Privacy-safe execution record, artifacts and sign-off |
| Production operator evidence | Unverified | No production-classified record | Approved deployment identity and production execution evidence |

## Delivered

- a versioned protocol with proof classifications and evidence effects;
- a closed structural JSON Schema for incident and rollback records;
- non-proof incident-response and rollback templates;
- CI-only fixtures that exercise ordered phase validation without making
  execution claims;
- an executable validator for identity separation, timelines, artifact
  provenance, redaction, sensitive-content rejection and claim convergence;
- a dedicated CI workflow that keeps the parent operational-readiness boundary
  in the validation chain.

## Evidence boundary

No incident-response exercise has been executed. No rollback has been executed.
The CI fixtures are synthetic and have no human attestation, approved
environment, deployment identity or execution claim. The templates and fixtures
cannot satisfy the parent proof requirements.

No production deployment, external reachability, deployed telemetry, SLO
attainment, page delivery, recovery effectiveness, RTO or RPO result is
verified. CAP-123 is not promoted and F4 remains pending.

## Verification discipline

Only successful checks attached to the current exact PR head are admissible as
repository validation evidence. A queued, cancelled, skipped, infrastructure-
failed or stale workflow run is neither a repository failure nor a passing
result and cannot advance this protocol, CAP-123 or F4. Retrying CI does not
change the evidence classification of templates or synthetic records.

## Next admissible proof

For either operator state to advance, add a record under
`docs/evidence/operator-drills/records/` using the canonical schema. A
human-attested record must identify an approved environment through opaque
subjects, preserve a complete ordered timeline, reference at least one
content-addressed artifact, pass redaction review and include independent
approval. Production classification additionally requires a deployment
identity and an explicit production-execution claim.
