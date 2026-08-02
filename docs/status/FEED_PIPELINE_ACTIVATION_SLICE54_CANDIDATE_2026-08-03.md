# Feed Pipeline Activation Governance — Slice 54 Candidate

Date: 2026-08-03
Status: Candidate pending exact-head CI
Parent: PR #232 / Slice 53
Issue: #233

## Included

- ADR-0090 and executable Slice 54 contract.
- Immutable exact-versioned feed pipeline definitions.
- DRAFT, ENABLED, PAUSED and terminal RETIRED lifecycle.
- Read-only dependency preflight with bounded operational results.
- Exact PUBLIC provider capability and lifecycle checks.
- Exact immutable provider-adoption and RSS/Atom parser profile hashes.
- Explicit rejection of HTTP auth profiles for PUBLIC feeds.
- Raw-evidence configured capability and reference verification.
- Public HTTP adapter constructibility without network execution.
- Exact deterministic feed-item extraction runtime-plan verification.
- Scheduler interval and dispatch-attempt bound verification without schedule creation.
- Dependency fingerprint recording and drift rejection.
- In-memory and transactional PostgreSQL definition repositories.
- Additive migration `20260803_0026` with empty-table downgrade guard.
- Disabled-by-default memory/PostgreSQL runtime composition with empty definition and parser-profile registries.
- Raw-evidence capability metadata wrapper with no storage fallback.
- Memory, runtime, PostgreSQL concurrency and migration behavior tests.
- Dedicated Feed Activation Governance CI.

## Preserved boundaries

- No concrete feed definition is registered in production.
- No feed is enabled and no scheduler record is created.
- Preflight performs no HTTP, DNS, socket, secret resolution, evidence write/read, acquisition dispatch, ingestion run or proposal write.
- No provider terms/egress, production deployment, SLO or rollback proof is claimed.
- No automatic editorial review, materialization, Case creation or publication occurs.
- No Admin UI, Case Builder, Flow Composer or phone-facing feed behavior is added.

## Validation policy

Do not call this slice PASS until Feed Activation Governance CI and every required parent provider/RSS/evidence/worker/API/MVP/global workflow pass on one exact runtime SHA. Keep the PR draft until that evidence exists.
