# ADR-0147: Stakeholder Gap Disclosure (CAP-038)

## Status

ACCEPTED

## Context

In high-stakes social, ethical, and institutional dilemmas, overall collective aggregate distributions alone may obscure significant perceptual divergence between different key stakeholder groups (e.g. directly affected citizens vs. general public, or domain practitioners vs. wider community). 

Without transparent stakeholder gap disclosure, consensus signals can be misleadingly flattened.

## Decision

1. **Stakeholder Segment Model**: Collective reveal snapshots support structured stakeholder segments with audited sample sizes, option distributions, and computed gap metrics (`gap_points`).
2. **Non-psychometric / Observed Segments**: Segments represent declared contextual roles (e.g., `DIRECTLY_AFFECTED`, `GENERAL_PUBLIC`, `PRACTITIONERS`) and never infer personality, ideology, or psychometric attributes.
3. **Disclosure Boundary**: Stakeholder gaps are presented only when statistical confidence thresholds and minimum segment sample sizes ($n \ge 30$) are satisfied to prevent identification or statistical noise.
4. **Localization**: Segment labels and gap descriptors are governed through canonical locale catalogs.

## Consequences

- Prevents artificial homogenisation of collective deliberation results.
- Preserves Commit First invariant (gaps are strictly post-commit).
- Enforces strict privacy thresholds per segment.
