# ADR-0149: Verified Institution Response and Impact Room (CAP-050)

## Status

ACCEPTED

## Context

KEFE completes its value loop in the IMPACT layer. When community deliberation produces a qualified Signal, targeted public or private institutions require a verified, auditable channel to publish official statements, commitments, policy changes, or factual clarifications.

Without a structured, verified institution response mechanism, public dialogue decays into unverified social media claims or unaccountable PR statements.

## Decision

1. **Structured Institution Response Types**:
   - `ACKNOWLEDGE`: Formal acknowledgment of the community signal.
   - `COMMITMENT`: Specific measurable pledge with a target milestone date.
   - `POLICY_CHANGE`: Official change in rules, regulations, or operations.
   - `FACTUAL_CLARIFICATION`: Contextual correction or data provision without changing policy.
   - `DECLINE_WITH_REASON`: Formal refusal with transparent reasoning.
2. **Verification & Provenance**:
   - Every statement requires an audited institutional authority proof (`authority_name`, `authority_role`, `verification_status: VERIFIED`).
   - Responses are immutably timestamped and linked to the underlying CaseVersion / Signal.
3. **Impact Transparency**:
   - Responses are exposed to users in the post-result Impact room without altering previous blind decision states.

## Consequences

- Closes the deliberation-to-impact feedback loop.
- Enforces strict institutional verification and accountability.
