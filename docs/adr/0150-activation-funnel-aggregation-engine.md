# ADR-0150: Activation Funnel Aggregation Engine (CAP-115)

## Status

ACCEPTED

## Context

Understanding user progression through the ethical deliberation cycle (from browsing to commit, result reveal, perspective exposure, and reflection/revision) is crucial for identifying UX friction, drop-offs, and deliberation quality.

However, analytics must preserve the KEFE privacy invariant: no user profiling, no raw response leakage, and no psychometric tracking.

## Decision

1. **Governed Funnel Stages**:
   - `WEIGH_STARTED`: User enters a case dilemma flow.
   - `DECISION_COMMITTED`: User blindly commits their choice.
   - `RESULT_REVEALED`: Collective result is unlocked and viewed.
   - `PERSPECTIVE_VIEWED`: Counter-arguments or peer perspectives are explored.
   - `DECISION_REVISED`: Reflection step is finalized.
2. **Aggregated Conversion Metrics**:
   - For each stage, the engine computes absolute counts, overall conversion rate relative to start, and sequential drop-off rates within an audited temporal window.
3. **Privacy Invariant**:
   - Calculations operate on session-level milestone timestamps only. Payloads never contain response contents, reasons, or user demographic tags.

## Consequences

- Provides actionable funnel observability for product and UX health.
- Strictly adheres to non-profiling and non-coercive privacy principles.
