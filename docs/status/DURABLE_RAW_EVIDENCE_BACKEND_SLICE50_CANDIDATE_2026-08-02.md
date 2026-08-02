# Durable Raw Evidence Backend — Slice 50 Candidate

Date: 2026-08-02
Issue: #225
Parent: PR #224 / Slice 49

## Candidate scope

This candidate adds a storage-vendor-neutral durable raw-evidence capability and runtime boundary:

- exact `DISABLED | EXTERNAL_DURABLE` runtime modes;
- immutable versioned backend profiles;
- canonical namespace, byte and timeout budgets;
- mandatory atomic put-if-absent, immutable objects and read-after-write verification;
- immutable profile/backend registries with duplicate/conflict rejection;
- provider-neutral `put_if_absent` and `read_exact` backend ports;
- redacted bounded write/read results;
- deterministic content-addressed object keys derived from KEFE-computed SHA-256;
- exact write then read-back verification before Slice 49 seal creation;
- bounded backend error translation without exception-text leakage;
- application-startup composition through `app.state.raw_source_evidence_store`;
- empty production profile/backend registries;
- explicit startup failure for missing external selection/profile/backend;
- no in-memory or disabled fallback from external durable mode.

## Validation state

Candidate only until all required workflows pass on one exact runtime SHA:

- Durable Raw Evidence Backend CI;
- Raw Source Evidence CI;
- Provider HTTP Capture CI;
- Provider HTTP Authentication CI;
- Provider Pinned Runtime CI;
- Provider HTTP Transport CI;
- Provider Secret Execution CI;
- Provider Admission CI;
- API CI;
- MVP Beta Gates;
- Global Readiness.

## Non-claims

This slice does not introduce or prove:

- S3, GCS, Azure, MinIO, filesystem or another concrete backend;
- bucket/container provisioning;
- credentials, signing or secret-manager integration;
- encryption or KMS custody;
- retention, deletion, legal hold or lifecycle policy;
- malware scanning, compression or replication;
- deployed storage availability, monitoring, SLOs, alerts or rollback drills;
- a real provider parser, adoption/auth profile or live external request;
- Admin provider UI, automatic editorial publication or phone-facing behavior.
