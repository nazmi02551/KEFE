# Provider Capability and Admission Control — Slice 43 Candidate

- Date: 2026-08-02
- Issue: #211
- Branch: `feature/provider-admission-control-slice43`
- Base: PR #210 / Slice 42 exact head
- Status: Candidate — exact-head CI pending

## Candidate capability

This slice adds a provider-neutral durable control plane that must authorize every source capture before an adapter is called:

- exact immutable versioned adapter capability;
- opaque secret reference only;
- explicit provider lifecycle;
- transactional fixed-window quota;
- closed/open/half-open circuit breaker;
- durable expiring capture permits;
- strict Source Acquisition integration.

## Locked behavior

- credential values never enter configuration, database rows, results or logs;
- allowed secret references are opaque `secret://`, `vault://`, `kms://` or `envref://` locators;
- configuration changes require a new versioned adapter code;
- provider lifecycle is `ENABLED`, `PAUSED`, `RETIRED`; retirement is terminal;
- provider capture admission is transactional and replica-safe;
- every admitted capture has one expiring durable permit;
- expired permits become `ABANDONED` and contribute failure before new admission;
- quota counts provider capture attempts;
- one half-open probe may be active for an adapter;
- capture success completes the permit before SourceArtifact persistence;
- typed and unexpected capture failures complete the permit as failure before return;
- permit completion uncertainty fails closed with no artifact persistence;
- adapter implementation registration alone is insufficient: the exact capability must also be configured and enabled;
- operational results exclude secret reference, credential, locator, provider response, payload, storage reference, title and user data.

## Candidate evidence included

- lifecycle, immutable configuration and secret-reference tests;
- quota/retry-after and window rollover tests;
- failure threshold, circuit-open and half-open probe tests;
- stale permit recovery tests;
- Source Acquisition blocked/fail-closed integration tests;
- PostgreSQL transactional quota, concurrent half-open and exact completion tests;
- reversible migration `20260802_0024`;
- architecture fitness.

## Explicit non-claims

This candidate does not prove or introduce:

- a credential resolver or secret value;
- a real provider adapter or network request;
- provider terms/rate-limit compliance;
- autonomous retry/backoff;
- Admin HTTP/UI;
- automatic Proposal review, projection or publication;
- dashboards, alerts, deployed SLOs or rollback readiness;
- Case Builder, Flow Composer or phone behavior.

Do not mark Slice 43 PASS until API CI, MVP Beta Gates and Global Readiness all succeed on the same runtime SHA.
