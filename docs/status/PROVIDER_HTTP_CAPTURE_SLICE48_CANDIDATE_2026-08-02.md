# Provider HTTP Capture Slice 48 — Candidate

- Date: 2026-08-02
- Issue: #221
- Parent PR: #220
- Parent exact head: `8821ce3b7ab9ccdc7d6fe1f94a22ba09ab44266b`
- Branch: `feature/provider-http-capture-slice48`
- Status: Candidate; exact-head CI pending

## Candidate capability

This slice adds the provider-neutral bridge between existing credential-aware source capture and the controlled authenticated HTTP runtime.

A provider-specific definition can only:

1. build one immutable public `OutboundHttpRequest` plan; and
2. parse one bounded `ProviderHttpResponse` into exact `CapturedSource`.

The generic wrapper validates the plan before HTTP execution, passes `SecretAccess` directly to `SecureProviderHttpExecutor` without reading it, preserves retryable/final HTTP classification and maps malformed planning/parsing behavior to bounded source-capture codes.

## Preserved boundaries

- no real provider definition or adapter;
- no adoption/auth profile;
- no live external request;
- no provider parser implementation;
- no raw-body storage;
- no autonomous retry;
- no secret-manager/OAuth/signing;
- no Admin provider UI;
- no automatic editorial publication;
- no deployed egress/SLO/alert/rollback claim;
- no phone-facing behavior.

## Validation required before ready-for-review

- Provider HTTP Capture CI;
- Provider HTTP Authentication CI;
- Provider Pinned Runtime CI;
- Provider HTTP Transport CI;
- Provider Secret Execution CI;
- Provider Admission CI;
- API CI;
- MVP Beta Gates;
- Global Readiness;
- all on one exact runtime SHA.
