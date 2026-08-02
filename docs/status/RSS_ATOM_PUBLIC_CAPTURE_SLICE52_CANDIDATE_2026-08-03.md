# RSS/Atom Public Capture — Slice 52 Candidate

Date: 2026-08-03
Status: Candidate pending exact-head CI
Parent: PR #228 / Slice 51
Issue: #229

## Included

- ADR-0088 and executable Slice 52 contract.
- Credential-free evidence-backed public HTTP capture adapter.
- Controlled provider HTTP transport with no credential binding.
- Raw evidence sealing before parser invocation.
- Trusted content hash and storage reference assembled only from the evidence seal.
- Reusable strict RSS 2.0 / Atom 1.0 capture definition.
- UTF-8-only XML profile with DTD, entity declaration, extra processing-instruction and XInclude rejection.
- Exact document, tree, item, text and attribute budgets.
- Feed-level metadata only; the exact validated request URL remains canonical.
- RSS/Atom, failure-order and full PUBLIC permit-to-SourceArtifact behavior tests.
- Architecture fitness and dedicated RSS Atom Public Capture CI.

## Preserved boundaries

- No concrete feed or provider adoption profile is registered.
- No PUBLIC provider capability is configured by default.
- No live external network request occurs in tests.
- No feed item is automatically converted into a proposal or Case.
- No editorial review, projection or publication is automated.
- No provider terms/compliance, production egress, deployment SLO, rollback or durability claim is made.
- No Admin provider UI, Case Builder, Flow Composer or phone-facing provider behavior is added.

## Validation policy

Do not call this slice PASS until the dedicated workflow and every required parent provider/evidence/API/MVP/global workflow pass on one exact runtime SHA. Keep the PR draft until that evidence exists.
