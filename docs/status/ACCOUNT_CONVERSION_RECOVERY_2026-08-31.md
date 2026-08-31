# Account conversion validation and recovery — 2026-08-31

Status: IMPLEMENTATION CANDIDATE / EXACT-HEAD CI PENDING / NO CAPABILITY
PROMOTION

Issue: #401  
Capabilities: CAP-084 (`IMPLEMENTED_PARTIAL`), CAP-095
(`ONGOING_MANDATORY`)  
Stack base: PR #400 exact-green head
`df4ebd2d40eff1b36f567f0b09fee60bea26f50f`

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
behavior. Full mobile regression evidence remains required.

Local evidence before publication:

- API Ruff: PASS;
- API contract sync and production runtime contract: PASS;
- complete API test suite: PASS (PostgreSQL-dependent tests skipped locally);
- account/session/Connected Alpha static contracts: PASS;
- capability portfolio and machine-readable contract validation: PASS;
- Flutter format, analyzer and tests: exact-head CI pending because the exact
  Flutter SDK is unavailable in the local workspace.

API CI, Mobile CI, MVP Beta Gates and Global Readiness must pass on one exact PR
head before this candidate is called PASS.

## Lifecycle

CAP-084 remains `IMPLEMENTED_PARTIAL`; CAP-095 remains `ONGOING_MANDATORY`.
This candidate does not update `docs/status/CURRENT.md`; human review,
production provider operation and capability governance remain separate gates.
