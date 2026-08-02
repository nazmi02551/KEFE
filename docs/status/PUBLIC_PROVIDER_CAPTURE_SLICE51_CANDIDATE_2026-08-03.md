# Public Provider Capture Slice 51 — Candidate

Date: 2026-08-03
Issue: #227
Parent: PR #226 / Slice 50

## Candidate scope

- exact `PUBLIC | SECRET_REF` provider credential mode;
- public capability has no secret reference;
- credentialed capability retains opaque allowed secret reference only;
- additive PostgreSQL migration preserving existing rows as `SECRET_REF`;
- cross-field database constraints;
- downgrade refusal while public capabilities exist;
- mode-aware active permit execution context;
- credentialed executor rejects public mode before resolver lookup;
- permit-bound public adapter registry and executor;
- exact mode-routing executor used by Source Acquisition;
- empty production public adapter registry;
- application state exposes public and routed capture composition;
- memory, architecture and PostgreSQL behavior evidence;
- dedicated Public Provider Capture CI and parent gate reruns.

## Candidate invariants

- Admission, quota, circuit breaker and permit completion are shared by both modes.
- Public capture cannot access secret resolution, auth-header decoration, DNS, TLS, raw-evidence storage or autonomous retry through this boundary.
- Credentialed execution cannot accept public permit context.
- No adapter runs without an active, unexpired permit for an enabled exact capability.
- Permit success is completed before SourceArtifact persistence.
- Operational results do not expose credential mode, secret reference or source payload.

## Explicit exclusions

No RSS/Atom parser, concrete public feed, live endpoint, provider/adoption/auth profile, production network egress, real durable backend, secret-manager integration, provider legal/compliance evidence, Admin provider UI, automatic editorial action/publication, Case Builder, Flow Composer or phone-facing behavior is claimed.

## Validation state

Candidate only until every required workflow passes on one exact runtime SHA. No PASS or merge claim is valid before exact-head evidence is recorded in PR #228.
