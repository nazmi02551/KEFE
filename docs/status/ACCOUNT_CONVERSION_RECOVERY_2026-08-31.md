# Account conversion validation and recovery — 2026-08-31

Status: IMPLEMENTATION CANDIDATE / EXACT-HEAD CI PASS / NO CAPABILITY
PROMOTION

Issue: #401  
Capabilities: CAP-084 (`IMPLEMENTED_PARTIAL`), CAP-095
(`ONGOING_MANDATORY`)  
Stack base: PR #400 exact-green head
`df4ebd2d40eff1b36f567f0b09fee60bea26f50f`
Implementation checkpoint: PR #402 head
`9c39e70e55096dadf68492890208c5769f83de48`

ADR: ADR-0145  
Contract: `docs/contracts/account-conversion-validation-recovery.v1.json`

## User-visible outcome

The optional account-protection flow no longer offers silent no-op actions for
an empty destination or incomplete code. The code field accepts six numeric
digits, and the Convert action becomes available only when that minimum is met.

An incorrect OTP keeps the user on the code step so it can be corrected without
requesting another challenge. An expired, used, missing or locked challenge
returns to the preserved destination/new-code path. Known states have bounded
Turkish and English guidance; unknown internal codes are not shown.

## Safety and Preview boundary

A transport failure during verification/merge requires a new code because the
client cannot prove whether the previous verification was consumed after a
lost response. This avoids blindly replaying an uncertain one-time operation.

Product Preview maps an incorrect sample code to the same recoverable account
failure shape. It remains explicit sample behavior and does not prove real OTP
delivery or production provider operation.

The account flow remains optional. Continue as guest, email/SMS channels,
guest-history merge, credential rotation/replacement, API, OpenAPI, persistence
and database semantics are unchanged.

## Evidence boundary

Controller coverage checks same-challenge recovery, terminal challenge reset,
transport uncertainty and local code validation. Turkish/English widget tests
check button states, localized recovery, corrected-code completion and Preview
behavior.

Local evidence before publication:

- API Ruff: PASS;
- API contract sync and production runtime contract: PASS;
- complete API test suite: PASS (PostgreSQL-dependent tests skipped locally);
- account/session/Connected Alpha static contracts: PASS;
- capability portfolio and machine-readable contract validation: PASS;
- Flutter format, analyzer, full mobile regressions and Android compile/artifact
  boundaries: PASS in exact-head CI.

Exact-head evidence on
`9c39e70e55096dadf68492890208c5769f83de48`:

- API CI, run `33358601212`: PASS;
- Mobile CI, run `33358601194`: PASS;
- MVP Beta Gates, run `33358601216`: PASS;
- Global Readiness, run `33358601219`: PASS;
- Capability Portfolio, Foundation Completion, Full Vision Delivery
  Convergence, Operational Readiness Evidence and CAP-123 Governance
  Reconciliation: PASS on the same head.

No APK is distributed for this small recovery slice.

## Lifecycle

CAP-084 remains `IMPLEMENTED_PARTIAL`; CAP-095 remains `ONGOING_MANDATORY`.
This candidate does not update `docs/status/CURRENT.md`; human review,
production provider operation and capability governance remain separate gates.
