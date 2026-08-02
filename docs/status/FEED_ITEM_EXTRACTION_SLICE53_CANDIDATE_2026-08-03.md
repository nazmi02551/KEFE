# Feed Item Extraction — Slice 53 Candidate

Date: 2026-08-03
Status: Candidate pending exact-head CI
Parent: PR #230 / Slice 52
Issue: #231

## Included

- ADR-0089 and executable Slice 53 contract.
- Provider-neutral raw-evidence read port.
- Immutable redacted evidence read model with owned byte copies.
- Exact storage-reference/content-hash consistency and SHA-256 read verification.
- In-memory and durable evidence read implementations.
- Explicit unconfigured-reader retryable failure.
- Deterministic RSS/Atom feed-item extraction stage.
- Strict SourceArtifact, run input and evidence-reference matching.
- Slice 52 strict RSS/Atom validation before item traversal.
- Bounded item identity, title, URL, timestamp, summary, proposal count and total output budgets.
- Duplicate item identity rejection.
- Deterministic proposal ordering and review-required risk code.
- Exact one-stage runtime builder for later explicit activation.
- In-memory/durable read, direct stage and full ingestion-worker behavior tests.
- Architecture fitness and dedicated Feed Item Extraction CI.

## Preserved boundaries

- Production ingestion runtime registry remains empty.
- No concrete provider or scheduled feed capture is registered.
- No live network occurs in tests or stage processing.
- No automatic proposal review, materialization, Case creation or publication occurs.
- No semantic classification, Claim extraction or AI summarization is introduced.
- No deployed object-storage, provider-compliance, SLO or rollback proof is claimed.
- No Admin UI, Case Builder, Flow Composer or phone-facing feed behavior is added.

## Validation policy

Do not call this slice PASS until Feed Item Extraction CI and every required parent evidence/RSS/ingestion/API/MVP/global workflow pass on one exact runtime SHA. Keep the PR draft until that evidence exists.
