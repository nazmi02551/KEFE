# ADR-0120: Operator drill evidence acceptance protocol

- Status: Accepted
- Date: 2026-08-06
- Foundation wave: F4
- Capability: CAP-123
- Parent: ADR-0119 and `docs/contracts/operational-readiness-evidence.v1.json`

## Context

ADR-0119 correctly separates repository and CI evidence from deployed telemetry,
external paging, incident-response execution and rollback execution. It names the
evidence kinds required for incident response and rollback, but a repository
record still needs deterministic acceptance rules. Without those rules, a
template, generated timeline or successful CI job could be mislabeled as a
human-operated exercise.

## Decision

KEFE will use
`docs/contracts/operator-drill-evidence-protocol.v1.json` and
`docs/contracts/operator-drill-evidence-record.schema.v1.json` as the canonical
acceptance boundary for incident-response and rollback evidence.

Four classifications are allowed:

| Classification | Meaning | Relevant operator requirement | Production proof |
|---|---|---:|---:|
| `TEMPLATE_ONLY` | Blank, reusable record shape | No | No |
| `CI_SIMULATED` | Synthetic validator fixture | No | No |
| `HUMAN_ATTESTED_NON_PRODUCTION` | Human-executed drill in an approved non-production environment | Yes | No |
| `HUMAN_ATTESTED_PRODUCTION` | Human-executed record bound to an approved production deployment | Yes | Yes, for the relevant execution record only |

A template is not an executed drill. CI cannot create a human attestation.
Independent approval is required for every human-attested classification.

## Acceptance rules

Every non-template record must have a bounded UTC timeline, ordered phases,
an outcome, privacy review and type-specific content. Incident-response records
must cover detection, acknowledgement, diagnosis, action and closure.
Rollback records must cover precheck, decision, execution, verification and
closure.

Human-attested records additionally require:

- an approved environment;
- opaque operator and approver subjects from an organization identity or ticket
  system;
- different operator and approver subjects;
- affirmative operator and approver attestations;
- at least one artifact with a content SHA-256 and capture time;
- a non-`NOT_EXECUTED` result;
- an execution claim matching the record type.

Production records also require `environment.kind=PRODUCTION`, a deployment
identity and `claims.production_executed=true`. A production classification
only supports the relevant incident or rollback execution claim. It does not
prove deployment reachability, SLO attainment, paging, RTO/RPO, or full F4
readiness.

## Privacy and security

Evidence records must not contain secrets, credentials, authorization headers,
access or refresh tokens, private keys, database connection strings, session
cookies, or raw customer data. Actors are represented by opaque subject
references rather than personal profile data. Artifact bodies are not stored in
the record; only controlled URIs, digests and capture timestamps are retained.

The executable checker rejects forbidden fields and value fragments. A
redaction review is mandatory for every non-template record.

## Current repository state

The repository contains two `TEMPLATE_ONLY` records and two `CI_SIMULATED`
fixtures. These exercise the record shape and rejection boundary only. There
are no human-attested evidence records, so incident response and rollback both
remain `OPERATOR_DRILL_PENDING`.

## Consequences

The protocol makes future evidence review reproducible and prevents CI from
self-certifying production readiness. A real operator still has to execute a
bounded exercise, preserve privacy-safe artifacts, obtain independent approval,
and add the resulting record before any operator-execution status can advance.

This ADR does not execute an incident-response exercise, perform a rollback,
verify production, establish an SLO, deliver a page, or promote CAP-123/F4.
