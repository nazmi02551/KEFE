# ADR-0209: Academic Research & Open Data Portal (CAP-036)

## Status

ACCEPTED

## Context

Computational social scientists, ethicists, and policy researchers require transparent, reproducible datasets to study collective intelligence and deliberative democracy. Under `KEFE-PB-001`, `KEFE-SEC-001`, and `KEFE-ANL-001`, KEFE provides an Open Science & Academic Research Portal exposing anonymized, $\epsilon$-differentially private aggregate telemetry and research corpora.

## Decision

1. **Research Corpus Taxonomy**:
   - `DELIBERATIVE_POLARIZATION_DATASET`: Temporal opinion migration vectors.
   - `ETHICAL_TRADE_OFF_CORPUS`: Machine-readable dilemmas and stakeholder matrices.
   - `ARGUMENT_GRAPH_TOPOLOGY`: Cross-perspective bridge resonation topologies.
   - `POLICY_OUTCOME_BENCHMARK`: Long-term retrospective impact validations.
2. **Privacy Guarantee**:
   - Strictly enforced differential privacy ($\epsilon \le 1.0, \delta \le 10^{-5}$) on all exported research query aggregates. Zero re-identification risk.

## Consequences

- Advances public scientific understanding of consensus algorithms.
- Uncompromising cryptographic defense of individual user privacy.
