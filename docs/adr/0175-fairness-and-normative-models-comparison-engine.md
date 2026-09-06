# ADR-0175: Fairness and Normative Models Comparison Engine (CAP-019)

## Status

ACCEPTED

## Context

Complex dilemmas cannot be reduced to a single ethical doctrine. In accordance with `KEFE-PB-001` (Product Bible) and `KEFE-CQB-001` (Content & Question Design Bible), every major case option should be evaluated across four foundational normative traditions:
1. `UTILITARIAN_MAX_WELFARE`: Utilitarianism (Bentham/Mill).
2. `DEONTOLOGICAL_CATEGORICAL_RIGHTS`: Deontological rights ethics (Kant).
3. `RAWLSIAN_MAXIMIN_EQUITY`: Distributive justice / veil of ignorance (Rawls).
4. `VIRTUE_ETHICS_CHARACTER`: Virtue & civic character ethics (Aristotle).

## Decision

1. **Multi-Model Scoring Framework**:
   - For each candidate option, scores are assigned in $[0.0, 1.0]$ across all four philosophical models.
   - Calculates primary ethical alignment archetype for the user's selected choice.

## Consequences

- Deepens civic philosophy literacy.
- Enables rich philosophical comparison without moral pontification.
