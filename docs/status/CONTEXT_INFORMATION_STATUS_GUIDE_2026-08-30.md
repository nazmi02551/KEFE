# Context information-status guide — 2026-08-30

Status: IMPLEMENTATION CANDIDATE / EXACT-HEAD CI PENDING / NO CAPABILITY PROMOTION

Issue: #395  
Pull request: #396  
Capabilities: CAP-069, CAP-070 (`IMPLEMENTED_PARTIAL`)  
Stack base: PR #394 exact-green head
`826f6efdf7cd3a07d980f95e2c53fe78b4ef99f6`

ADR: ADR-0142  
Contract: `docs/contracts/context-information-status-guide.v1.json`

## User-visible outcome

The Context screen explains the four existing information states in a compact,
optional disclosure. The explanation remains attached to information blocks
and explicitly does not verify linked sources. Neutral source previews also
show their existing publication date when one is available.

## Boundary

This slice does not add source verification, a truth or confidence score,
ranking, recommendation, new editorial methodology, API/schema changes,
external URL launching, Signal or Impact. Publication date is provenance only.

## Evidence boundary

The repository guard and focused widgets must prove Turkish/English parity,
shared legacy/progressive presentation, stable semantics, absent-date omission,
light/dark compatibility and enlarged-text safety. The four required workflows
must pass on one exact PR head before this candidate is called PASS.

CAP-069 and CAP-070 remain `IMPLEMENTED_PARTIAL`. This candidate does not
update `docs/status/CURRENT.md`.
