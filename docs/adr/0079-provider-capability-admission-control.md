# ADR-0079: Provider Capability, Credential Mode and Admission Control

- Status: Accepted
- Date: 2026-08-02
- Amended: 2026-08-03 by ADR-0087
- Decision owners: KEFE Product and Engineering
- Related: ADR-0075, ADR-0076, ADR-0078, ADR-0087, Issues #180, #211 and #227

## Context

The provider-neutral acquisition runtime can schedule, supervise and observe content supply, but a real provider adapter must not be activated merely by registering code. Before any network provider is adopted, KEFE needs one authoritative control plane for capability lifecycle, credential mode, quota admission and circuit state.

Credential values must never enter domain objects, database rows, operational results or logs. Some providers use an opaque deployment-specific secret reference; public providers require no credentials. Provider SDK responses and source payloads must remain outside the control plane. Quota and circuit decisions must be transactional so multiple process replicas cannot exceed configured admission or send multiple half-open probes.

## Decision

Introduce a durable provider capability aggregate and capture-permit ledger under the Knowledge boundary.

### Capability configuration

A capability is identified by the exact immutable versioned `adapter_code` already used by Source Acquisition. Its immutable configuration contains:

- exact credential mode `PUBLIC` or `SECRET_REF`;
- no secret reference for `PUBLIC`, or an opaque allowed `secret_ref` for `SECRET_REF`;
- fixed-window quota limit and window duration;
- consecutive-failure threshold;
- circuit-open duration;
- capture-permit TTL.

A secret reference is a locator for a deployment-specific resolver. It is not a secret value and is never returned in an operational result. A public capability cannot contain a secret reference. Existing persisted capabilities migrate as `SECRET_REF` without changing their behavior.

Capability lifecycle is explicit:

- `ENABLED`;
- `PAUSED`;
- `RETIRED`.

`RETIRED` is terminal. Configuration is not edited in place; changed semantics, including a credential-mode change, require a new versioned adapter code.

### Operational state

The aggregate maintains:

- current fixed-window start and admitted count;
- consecutive failure count;
- circuit state `CLOSED`, `OPEN` or `HALF_OPEN`;
- circuit-open timestamp;
- updated timestamp.

Quota windows roll forward from the configured fixed boundary. Admission counts provider requests, not SourceArtifact writes. These rules are identical for public and credentialed providers.

### Capture permits

Every adapter call requires a durable permit with states:

- `ACTIVE`;
- `SUCCEEDED`;
- `FAILED`;
- `ABANDONED`.

Admission is one transaction that locks the capability, recovers expired active permits, rolls the quota window, evaluates lifecycle/circuit/quota and, when allowed, increments the window count and inserts one active permit.

An expired permit is marked `ABANDONED` and contributes one failure before a new decision. Permit completion requires exact permit id and adapter code while the permit is active and unexpired. The active execution context also carries the exact credential mode so public and credentialed executors cannot silently cross paths.

### Circuit behavior

- `CLOSED`: admits while quota remains.
- At the failure threshold, the circuit becomes `OPEN`.
- `OPEN`: denies until the configured open duration elapses.
- When the duration elapses, the next admission becomes the sole `HALF_OPEN` probe.
- While that probe is active, other admissions are denied.
- Probe success closes the circuit and resets failures.
- Probe failure reopens the circuit from the failure time.

### Source Acquisition integration

Production composition uses a strict admission service backed by an empty capability registry. Therefore an adapter cannot run unless both:

1. its exact adapter implementation is registered in the registry for its credential mode; and
2. its exact provider capability is explicitly configured and enabled.

`SourceAcquisitionService` requests a permit immediately before adapter capture. Denials map to bounded blocked/retryable acquisition outcomes. A mode-aware executor validates the active permit and routes only `PUBLIC` contexts to the public adapter registry and only `SECRET_REF` contexts to the credentialed executor. The credentialed executor rejects public mode before any resolver lookup.

Capture success closes the permit before SourceArtifact persistence. Typed and unexpected capture failures close it as failure before returning. If permit completion cannot be proven, acquisition fails closed and no SourceArtifact is persisted.

### Privacy

Control-plane and permit operational results may expose only exact adapter code, bounded outcome/reason codes, permit id, circuit state, retry-after and timestamps. They never expose:

- credential mode in public operational results;
- secret reference;
- credential value;
- external locator;
- provider response;
- source payload;
- raw storage reference;
- title;
- user data.

## Consequences

### Positive

- Provider activation becomes explicit and fail-closed.
- Public providers do not require fake credentials or bypass governance.
- Multiple replicas share one transactional quota/circuit state.
- Circuit probes and permit recovery are deterministic.
- Credential values remain outside persisted/runtime domain data.
- Source capture failures feed operational governance without being treated as truth.

### Trade-offs

- Credentialed adapters still require a deployment-specific secret resolver.
- Public adapters require a separate explicit registry and execution path.
- Fixed-window quota is intentionally simpler than provider-specific rolling algorithms.
- Local controls do not prove provider terms or rate-limit compliance.

## Non-goals

- actual secrets or credential resolution for public providers;
- concrete provider SDK/network adapters;
- RSS/Atom parsing;
- provider compliance certification;
- autonomous retry/backoff;
- Admin HTTP/UI;
- automatic editorial action or publication;
- dashboards, alerts, deployed SLOs or rollback proof;
- Case Builder, Flow Composer or phone behavior.
