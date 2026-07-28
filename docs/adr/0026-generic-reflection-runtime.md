# ADR-0026 — Generic Reflection Runtime and Completion Boundary

- Status: Accepted
- Date: 2026-07-29
- Depends on: ADR-0019, ADR-0023, ADR-0024, ADR-0025

## Context

ADR-0025 made DecisionRevision, actual Exposure, server-classified Intervention and generic DecisionDelta executable. `PRINCIPLE_CONTEXT_RETEST` can therefore move from an initial Decision through Context to a later Decision without introducing a Case type.

The pinned Flow already contains the `REFLECTION` primitive, but the runtime intentionally returns `FLOW_REFLECTION_RUNTIME_PENDING`. The next slice must complete the Golden User Loop without turning Reflection into a second decision engine, a causal attribution engine, or a new Case-specific screen family.

## Decision

### 1. Reflection is a generic Flow primitive

`REFLECTION` is evaluated from the session-pinned Flow and actor-owned Decision lineage. Runtime behavior must not branch on BaseFormat, Domain, Case slug or named scenario.

### 2. Reflection does not create a DecisionRevision

A DecisionRevision represents a committed decision at a particular lineage state. Reflection observes that lineage; it does not mutate a committed revision and does not create another revision merely because the user viewed or completed Reflection.

A later decision requires an explicit later `DECISION` Flow Step and the ADR-0025 revision commit path.

### 3. Reflection read model is server-derived and non-causal

For an actor-owned session, the server may derive a privacy-minimal Reflection read model from immutable lineage metadata, including:

- revision count;
- latest committed revision identity;
- latest DecisionDelta identity when one exists;
- whether the latest Delta contains any changed question IDs;
- changed-question count;
- linked Intervention count and type codes;
- the contribution classes of the compared revisions.

The read model must not claim that an Intervention caused a change. Wording and API semantics are descriptive: "between these revisions", not "because of this intervention".

The generic Reflection read model does not expose private reason text or raw response values.

### 4. Reflection completion is its own immutable record

Completing a Reflection Step creates an immutable, actor-scoped `ReflectionCompletion` pinned to:

- WeighSession;
- CaseVersion;
- Flow Step code;
- latest DecisionRevision at completion;
- latest DecisionDelta when present;
- idempotency key;
- completion timestamp.

Completion means only that the user completed the Reflection Step at that lineage cursor. It does not mean agreement with an argument, acceptance of a causal explanation, advocacy support, or a new decision.

### 5. Completion is lineage-cursor aware

A `REFLECTION` Step is:

- `BLOCKED` while predecessors are unsatisfied;
- `READY` when predecessors are satisfied and there is no completion for the current latest DecisionRevision;
- `COMPLETED` when an immutable completion exists for the current latest DecisionRevision.

If a later DecisionRevision is subsequently committed, an older completion does not complete Reflection for the new lineage cursor. The Step becomes `READY` again when reachable.

This rule supports V0→V1→V2→V3+ decision journeys without mutating historical Reflection records.

### 6. Reflection is not Exposure or Intervention by default

Rendering or completing the user's own derived Reflection summary is not automatically a methodology-significant Intervention and does not change `CORE_PRE_RESULT` / `EXPOSED` contribution classification.

If a future Reflection experience introduces external evidence, counterarguments, institution responses or other decision-relevant content, those encounters must use the normal Exposure/Intervention model explicitly.

### 7. Reflection is not Signal or Advocacy

Reflection records are actor-private product state by default and do not enter collective result samples, Signal qualification, advocacy support counts or Impact routing.

Aggregate research use requires a separately approved methodology/privacy contract.

### 8. HTTP boundary

The first implementation slice will expose actor-scoped endpoints equivalent to:

- `GET /v1/weigh-sessions/{session_id}/reflection-steps/{step_code}` — server-derived read model;
- `POST /v1/weigh-sessions/{session_id}/reflection-steps/{step_code}/complete` — immutable/idempotent completion.

Both derive authority from the actor-owned session and pinned Flow. The client cannot select the lineage cursor, mark a blocked Step complete, or provide its own Delta/Intervention classification.

### 9. Flutter remains Flow-driven

When server Flow returns a `REFLECTION` Step as `READY`, Flutter renders one reusable Reflection primitive component and obtains the read model from the Reflection endpoint.

After successful completion it refreshes Flow runtime. No `retest`, `dilemma`, `political`, or other Case-specific Reflection screen/controller is permitted.

Offline support may retain a pending completion command with its idempotency key, but the client must not fabricate a Reflection read model for a lineage cursor it has not obtained from the server.

## Consequences

- `PRINCIPLE_CONTEXT_RETEST` can become fully executable without changing its Case type or introducing a Reflection-specific Case class.
- Reflection remains structurally separate from DecisionRevision and DecisionDelta.
- Historical Reflection completion is reproducible because it is pinned to an immutable lineage cursor.
- A later revision naturally reopens Reflection without rewriting history.
- Signal, Impact and advocacy semantics remain uncontaminated by private Reflection actions.

## Rejected alternatives

### Reflection creates another DecisionRevision

Rejected. A revision must correspond to an explicit Decision Step, otherwise Reflection would silently alter sample semantics.

### Reflection stores a mutable `reflected=true` flag on WeighSession

Rejected. It loses the lineage cursor and cannot represent later revisions or repeated reflection.

### Client decides whether a decision changed

Rejected. Delta authority is server-side and pinned to immutable revisions.

### Reflection attributes change to the most recent Intervention

Rejected. ADR-0025 deliberately makes Delta non-causal.

### Separate Reflection implementations per BaseFormat/Case

Rejected. It violates the case-agnostic composition model.
