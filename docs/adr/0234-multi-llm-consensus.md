# ADR-0234: Cross-Model Multi-LLM Deliberation Consensus (CAP-094)

## Status

ACCEPTED

## Context

Relying on a single proprietary AI foundation model creates architectural vendor lock-in and propagates blind-spots unique to that provider's training alignment. Under `KEFE-PB-001`, `KEFE-ETG-001`, and `KEFE-ENG-001`, KEFE provides a Multi-LLM Deliberation Consensus engine querying an ensemble of heterogeneous models (e.g., Gemini, Claude, Llama) to synthesize verified common factual ground.

## Decision

1. **Ensemble Agreement Level Taxonomy**:
   - `UNANIMOUS_CROSS_MODEL_CONSENSUS`: All audited models agree on factual synthesis.
   - `MAJORITY_CONVERGENT_SYNTHESIS`: Substantial agreement with minor stylistic nuance.
   - `MODEL_DIVERGENCE_REVIEW_REQUIRED`: Significant disagreement between models requiring human editorial CQB.
2. **Neutrality Invariant**:
   - Provider diversity is mandatory: At least 3 distinct model architectures must be evaluated.

## Consequences

- Neutralizes single-model hallucination patterns and provider-specific bias.
- Guarantees high-integrity, provider-neutral deliberative synthesis.
