# ADR-0146 — Non-coercive Insufficient Information and Missing Options Response

- Status: CANDIDATE
- Date: 2026-08-31
- Issue: #403
- Capability: CAP-011
- Parent: PR #402 / `feature/account-conversion-validation-recovery` (`091e6329`)

## Context

In complex ethical, civic, legal, and personal dilemmas, forcing users to choose among predefined choices (e.g., Choice A vs. Choice B) when they legitimately lack essential factual context or when they believe the dilemma presents a false dichotomy introduces measurement distortion (forced-choice artifact).

KEFE's foundational philosophy requires authentic, uncoerced decision recording. Forcing an arbitrary selection undermines:
1. The integrity of individual reflection (ME layer);
2. The accuracy of collective divergence models (WE layer);
3. Downstream signal qualification (SIGNAL layer).

## Decision

1. **Canonical Alternative Response Types:**
   Support standardized, non-coercive alternative responses alongside predefined question options:
   - `OPT_OUT_INSUFFICIENT_INFO`: The user states they lack sufficient factual or contextual information to make a definitive choice.
   - `OPT_OUT_MISSING_OPTIONS`: The user states that the presented choices do not encompass their stance or represent an incomplete dilemma.

2. **Validation Engine (`services/api`):**
   - For `SINGLE_CHOICE` question primitives, responses matching `OPT_OUT_INSUFFICIENT_INFO` and `OPT_OUT_MISSING_OPTIONS` are recognized as valid responses.
   - The decision commit pipeline records the uncoerced response truthfully with complete lineage and immutable hash preservation.
   - Reason capture remains fully enabled, allowing users to optionally explain what information was missing or how options were incomplete.

3. **Client Presentation (`apps/mobile`):**
   - Question cards present dedicated, non-intrusive alternative action options clearly separated from the primary dilemma choices.
   - Selecting an alternative response seamlessly enables the private reason capture and Commit First flow without forcing a mock option.
   - Turkish and English localization strings provide clear, neutral copy.

4. **Invariants Preserved:**
   - **Commit First:** Results and perspectives remain completely isolated until the user commits their choice or alternative response.
   - **No Causal/Psychometric Inference:** The system describes recorded responses without labeling the user as indecisive or biased.
   - **Immutable CaseVersion:** No named case types or custom schema mutations; uses generic primitive validation.

## Verification

- Machine-readable contract: `docs/contracts/insufficient-info-response.v1.json`;
- Decision service response validation tests;
- Mobile decision card and localization tests;
- Portfolio validation gate `validate_capability_portfolio.py`.

## Lifecycle

Advances CAP-011 from `PROPOSAL_REVIEW` towards verified implementation without unproven promotion.
