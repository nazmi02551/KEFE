# ADR-0079: Provider Capability, Secret-Reference and Admission Control

- Status: Accepted
- Date: 2026-08-02
- Decision owners: KEFE Product and Engineering
- Related: ADR-0075, ADR-0076, ADR-0078, Issues #180 and #211

## Context

The provider-neutral acquisition runtime can now schedule, supervise and observe content supply, but a real provider adapter must not be activated merely by registering code. Before any network provider is adopted, KEFE needs one authoritative control plane for capability lifecycle, credential reference, quota admission and circuit state.

Credential values must never enter domain objects, database rows, operational results or logs. Provider SDK responses and source payloads must remain outside the control plane. Quota and circuit decisions must be transactional so multiple process replicas cannot exceed configured admission or send multiple half-open probes.

## Decision

Introduce a durable provider capability aggregate and capture-permit ledger under the Knowledge boundary.

### Capability configuration

A capability is identified by the exact immutable versioned `adapter_code` already used by Source Acquisition. Its immutable configuration contains:

- opaque `secret_ref` using an allowed reference scheme;
- fixed-window quota limit and window duration;
- consecutive-failure threshold;
- circuit-open duration;
- capture-permit TTL.

The reference is a locator for a future deployment-specific resolver. It is not a secret value and is never returned in an operational result.

Capability lifecycle is explicit:

- `ENABLED`;
- `PAUSED`;
- `RETIRED`.

`RETIRED` is terminal. Configuration is not edited in place; changed semantics require a new versioned adapter code.

### Operational state

The aggregate maintains:

- current fixed-window start and admitted count;
- consecutive failure count;
- circuit state `CLOSED`, `OPEN` or `HALF_OPEN`;
- circuit-open timestamp;
- updated timestamp.

Quota windows roll forward from the configured fixed boundary. Admission counts provider requests, not SourceArtifact writes.

### Capture permits

Every adapter call requires a durable permit with states:

- `ACTIVE`;
- `SUCCEEDED`;
- `FAILED`;
- `ABANDONED`.

Admission is one transaction that locks the capability, recovers expired active permits, rolls the quota window, evaluates lifecycle/circuit/quota and, when allowed, increments the window count and inserts one active permit.

An expired permit is marked `ABANDONED` and contributes one failure before a new decision. Permit completion requires exact permit id and adapter code while the permit is active and unexpired.

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

1. its exact adapter implementation is registered; and
2. its exact provider capability is explicitly configured and enabled.

`SourceAcquisitionService` requests a permit immediately before adapter capture. Denials map to bounded blocked/retryable acquisition outcomes. Capture success closes the permit before SourceArtifact persistence. Typed and unexpected capture failures close it as failure before returning. If permit completion cannot be proven, acquisition fails closed and no SourceArtifact is persisted.

### Privacy

Control-plane and permit operational results may expose only exact adapter code, bounded outcome/reason codes, permit id, circuit state, retry-after and timestamps. They never expose:

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
- Multiple replicas share one transactional quota/circuit state.
- Circuit probes and permit recovery are deterministic.
- Credentials remain outside persisted/runtime domain data.
- Source capture failures feed operational governance without being treated as truth.

### Trade-offs

- Real adapters still require a deployment-specific secret resolver.
- Fixed-window quota is intentionally simpler than provider-specific rolling algorithms.
- Local controls do not prove provider terms or rate-limit compliance.

## Non-goals

- actual secrets or credential resolution;
- provider SDK/network adapters;
- provider compliance certification;
- autonomous retry/backoff;
- Admin HTTP/UI;
- automatic editorial action or publication;
- dashboards, alerts, deployed SLOs or rollback proof;
- Case Builder, Flow Composer or phone behavior.