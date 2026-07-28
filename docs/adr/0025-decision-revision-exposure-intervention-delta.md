# ADR-0025 — DecisionRevision, Exposure, Intervention and generic DecisionDelta

**Status:** Accepted  
**Date:** 2026-07-29

## Context

ADR-0019 defines the generic lineage `DecisionRevision → Exposure/Intervention → DecisionRevision → DecisionDelta`. ADR-0023 exposes a CaseVersion-pinned generic Flow runtime, but deliberately stops at the second Decision Step with `FLOW_DECISION_REVISION_REQUIRED`. ADR-0024 makes Flutter obey that runtime rather than inventing a fixed fallback.

The next slice must make materially different flows such as `PRINCIPLE_CONTEXT_RETEST` executable without turning WeighSession into a case-specific state machine and without mutating the first committed judgment.

The model must also preserve the distinction already locked in the product baseline:

- Context is decision-relevant information.
- Reveal is availability/presentation of previously withheld information.
- Exposure records that the Actor actually encountered information/result/perspective.
- Intervention is an exposure/event intentionally analyzed as a possible decision-change trigger.
- DecisionRevision is an immutable decision state at a defined exposure point.
- DecisionDelta is the generic difference between two immutable revisions.

## Decision

### 1. WeighSession remains the lineage container

`WeighSession` remains the actor-scoped container pinned to one CaseVersion and its immutable resolved Flow.

The existing session `COMMITTED` state means the **initial Commit barrier has completed**. It does not mean the session can never contain a later DecisionRevision.

No later revision may mutate the original committed response rows or the original private reason.

### 2. Initial Commit materializes DecisionRevision #1

A successful existing Commit transaction must also materialize the first immutable `DecisionRevision` from the committed session state.

Revision #1 records at least:

- actor/session/CaseVersion identity,
- monotonic `revision_no = 1`,
- the first Decision Flow Step code,
- committed response snapshot,
- private reason snapshot when present,
- commit time,
- exposure cursor/state at commit,
- contribution class.

The initial Commit endpoint remains backward compatible. Creating Revision #1 is an additional durable invariant, not a second client action.

Idempotent Commit replay must not create a second Revision #1.

### 3. Later Decision Steps use separate revision drafts

A later `DECISION` Flow Step never reopens the original WeighSession response rows.

Mutable work for that Step is stored as a **revision draft** scoped to:

`Actor + WeighSession + Flow Step`.

The revision draft may capture response values and private reason state. Once committed it becomes an immutable `DecisionRevision`; the draft cannot mutate the committed revision.

A committed DecisionRevision is unique for a given `session_id + flow_step_code`. `revision_no` is monotonic within the session.

### 4. Flow Step identity is authoritative

DecisionRevision execution is driven by the session-pinned CaseVersion `resolved_flow`.

The server validates that:

- the requested Step exists in the pinned Flow,
- its Primitive is `DECISION`,
- all blocking predecessors are satisfied,
- the Step has not already been committed,
- required response/schema rules are satisfied.

Clients cannot submit CaseVersion identity, actor identity, revision number, predecessor completion or intervention classification as authority.

Live Content Configuration is not consulted to reinterpret an existing session.

### 5. Exposure is append-only evidence of encounter

Exposure is actor-scoped, CaseVersion-pinned and append-only.

A fetch alone does not universally mean the user actually saw something.

For content that can be prefetched or is public before a session-specific interaction, such as Context, the client records a session Flow-Step exposure only after the corresponding UI is actually rendered/encountered.

For actor-scoped post-Commit payloads served on demand, a successful server delivery may atomically record exposure because the server is delivering the gated material to that Actor/session. This applies to current Reveal/Perspective delivery semantics.

Exposure recording is idempotent for the same client idempotency key but may retain multiple distinct encounters over time.

Exposure must retain enough provenance to identify at least:

- session/CaseVersion/Actor,
- Flow Step,
- exposed resource category and optional resource identity,
- occurred time,
- server-derived capability/primitive context,
- opaque metadata that does not become a case-specific schema.

### 6. Intervention is separate from Exposure

Not every Exposure is necessarily an Intervention.

An `Intervention` is the server-validated exposure/event selected by Flow/methodology semantics as a candidate trigger between two revisions.

An Intervention may reference one Exposure or a non-exposure event. Its generic metadata may contain dimension/type/capability context, but introducing ActorDelta, LegalDelta, CostDelta, AgeDelta or other dimension-specific engines is forbidden.

For the first retest slice, a Context Step positioned after a committed Decision and before a later Decision is methodology-significant by composition. Its recorded Flow-Step Exposure is promoted to an Intervention for that revision transition.

A future capability or methodology version may refine this rule without creating case-specific runtime branches.

### 7. Exposure-aware Flow runtime v2

The existing Primitive-driven runtime is extended, not replaced.

First `DECISION`:
- READY before initial Commit.
- COMPLETED when Revision #1 exists.

Later `DECISION`:
- BLOCKED while predecessors are unsatisfied.
- READY when predecessors, including required intervention exposure, are satisfied and no revision exists for that Step.
- COMPLETED when a DecisionRevision exists for that Step.
- it is no longer intrinsically `UNSUPPORTED` once this ADR is implemented.

`CONTEXT` before the first Decision remains informational/non-blocking unless a future pinned capability says otherwise.

`CONTEXT` located between a completed Decision and a later Decision is exposure-aware:
- READY when reachable but not yet exposed,
- COMPLETED after server-recorded Flow-Step Exposure/Intervention.

`COLLECTIVE_RESULT` continues to expose no result payload through Flow runtime. A successful Reveal records result Exposure. If a future Flow contains a later Decision after that result, the recorded Exposure can participate in the same generic Intervention lineage.

### 8. Contribution classes are derived, not client supplied

DecisionRevision stores a server-derived contribution class needed by later WE/Signal work.

Initial semantics:

- `CORE_PRE_RESULT`: no Collective Result/Signal exposure exists before that revision.
- `EXPOSED`: Collective Result/Signal exposure exists before that revision.
- `ADVOCACY_SUPPORT`: never a DecisionRevision class; advocacy support is a separate action/domain concept.

The client cannot select or override contribution class.

### 9. DecisionDelta is generic and reproducible

A `DecisionDelta` links:

- one `from_revision`,
- one `to_revision`,
- zero or more Interventions between them,
- a generic response-level diff snapshot,
- methodology/version provenance when methodology-specific interpretation is added.

The durable delta stores generic before/after changes or a reproducible equivalent. Private reason text must not become public merely because a Delta exists.

Delta creation does not claim causality. It records change observed across an exposure/intervention lineage.

### 10. Security, privacy and idempotency

All revision/exposure/intervention commands are authenticated and actor-scoped to the owning WeighSession.

Another Actor's session must remain indistinguishable from not found.

Initial Commit idempotency remains authoritative for Revision #1. Later revision commits and explicit exposure recording require independent actor/session-scoped idempotency keys.

Exposure/Intervention/Delta APIs must not leak another Actor's private response or reason state.

### 11. First implementation boundary

The first implementation under this ADR must provide one generic vertical slice sufficient to make `PRINCIPLE_CONTEXT_RETEST` executable end to end:

1. initial Commit creates Revision #1,
2. intermediate Context is explicitly exposed and becomes Intervention,
3. later Decision draft is edited and committed as Revision #2,
4. Flow runtime reports the later Decision COMPLETED,
5. generic DecisionDelta links Revision #1 → Intervention → Revision #2.

This slice must work through the same server runtime and Flutter Primitive rendering model. It must not introduce a `principle_case`, `retest_case` or other runtime Case Type.

Reflection remains a separate pending capability after the second revision unless implemented by a later ADR/slice.

## Consequences

- Existing initial Commit semantics stay backward compatible while gaining immutable revision lineage.
- Historical initial responses remain immutable and reproducible.
- Flow runtime can move `PRINCIPLE_CONTEXT_RETEST` from PARTIAL at DecisionRevision to executable through its second Decision Step.
- Context/result/perspective delivery can feed one generic Exposure/Intervention mechanism.
- Later WE/Signal work receives the contribution-class boundary required to keep pre-result and exposed decisions separate.
- Decision change is measured without claiming that the Intervention caused the change.
- Dimension-specific delta engines and case-specific retest controllers remain forbidden.