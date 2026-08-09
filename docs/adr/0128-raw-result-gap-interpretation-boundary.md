# ADR-0128 — RAW Collective Result stays descriptive-only

- Status: Candidate
- Date: 2026-08-09
- Wave: F4
- Related: #356, PR #350, PR #355

## Context

Connected Alpha introduces a live `RAW` Collective Result when no reviewed `TRUSTED` snapshot exists. The RAW layer is intentionally limited to observed committed-option aggregation and carries no representativeness, statistical-confidence, Signal, Impact, ideology or normative-authority claim.

The mobile Result card historically rendered `KEFE Gap` whenever a selected option and a leading option existed. That presentation is interpretive: it describes a choice as leading, majority-like, or separated from the leader. Applying it to a RAW population can overstate a very small or otherwise unqualified participation set even when the methodology footer says that representativeness is not claimed.

The Internal Alpha product authority also preserves the rule that Collective Result/Consensus must not shortcut into methodology-qualified Signal.

## Decision

`RevealResultCard` SHALL render the KEFE Gap interpretive insight only for `layer == TRUSTED`.

For `RAW`:

- observed option distribution remains visible;
- the user's committed decision remains visible;
- sample size remains visible through the methodology footer;
- the explicit RAW methodology wording remains visible;
- KEFE Gap interpretation is hidden.

Unknown or future layers fail closed and do not inherit TRUSTED interpretation.

No sample-size threshold is introduced in the mobile client. Qualification belongs to the evidence/methodology layer, not to a presentation magic number.

## Why layer gating instead of `n >= X`

A sample-size threshold alone cannot establish sampling quality, representativeness, weighting quality, cohort integrity or methodology review. Hardcoding an arbitrary number into mobile would also create a second qualification authority outside the methodology system.

The result layer already carries the intended evidence boundary. Mobile therefore consumes that authority instead of inventing a parallel rule.

## Preserved behavior

- TRUSTED result distribution and KEFE Gap remain unchanged.
- RAW distribution remains visible.
- Result arithmetic is unchanged.
- Commit First and Blind First are unchanged.
- Flow runtime and immutable CaseVersion behavior are unchanged.
- Product Preview / production isolation is unchanged.
- My KEFE remains descriptive-only.
- This decision does not assert that TRUSTED is automatically Signal or Impact.

## Verification

The focused mobile test must prove:

1. RAW renders distribution + methodology but no `reveal-gap-insight`;
2. TRUSTED still renders `reveal-gap-insight`;
3. an unknown future layer does not render `reveal-gap-insight`;
4. the executable repository guard rejects a client-side sample-size threshold;
5. verification reuses the existing `Mobile CI` workflow rather than creating another dedicated workflow.

## Consequences

The first Connected Alpha can show real shared participation truthfully without turning two or twenty early participants into a stronger social interpretation than the evidence supports. Later methodology-qualified result layers may enable richer interpretation through explicit product/methodology authority rather than hidden client heuristics.
