# ADR-0053 — Premium post-Commit social participation visual slice 15

- Status: Accepted
- Date: 2026-07-31
- Issue: #125
- Stack base: PR #124 status head `e1391a0271b75f43dd6aa91fa0fa2eac033e4e91`
- Inherited verified Slice 14 runtime: `95822fda8a5bb26c552f5fc4f35f54fa9fcb1333`
- Extends: ADR-0038, ADR-0039, ADR-0041, ADR-0052

## Context

The premium Decision Journey, Reveal, Perspective, Activity/My KEFE, shell, trust controls and Blind First sharing surfaces have converged onto the shared KEFE visual system. Two post-Commit social participation surfaces remain visibly behind that baseline:

1. `ConsensusSection`, which renders the existing consensus-card participation and aggregate-result states.
2. `CommunityReasonSection`, which renders the existing structured reason publication, moderation receipt, reaction and report states.

Both already depend on committed session/CaseVersion context exposed by `PerspectiveSection`. Their product behavior already exists and must not be broadened by a visual pass.

Current presentation debt is concrete:

- generic `Card` framing rather than semantic KEFE surfaces;
- direct dark-only `KefeColorTokens` inside Consensus;
- raw bordered containers and stock hierarchy inside Community Reasons;
- continuous indeterminate progress indicators that are visually inconsistent and can keep shared/offstage Flutter surfaces unsettled;
- weak visual distinction between trust/methodology, action, result and moderation states.

This ADR does not authorize new community or consensus capabilities.

## Decision

1. Consensus and Community Reasons are one visual slice because they are adjacent post-Commit participation surfaces under the same committed-session boundary.
2. Existing feature gates, controllers, repository calls, session binding and CaseVersion binding remain authoritative.
3. `ConsensusSection` preserves its existing states: `idle`, `loading`, `empty`, `blocked`, `errorRetryable`, `eligible`, `submitting`, `participated`.
4. Existing Consensus card proposition, stance codes, reason-tag codes, max reason tags, participation state, aggregate stance distribution, reason-pattern distribution, contribution class, sample size and provenance note are display inputs only. This slice must not create a new aggregate, score, ranking, recommendation or interpretation.
5. Existing Consensus submit/retry behavior and keys remain stable, including `consensus-section`, `consensus-card-<versionId>`, `consensus-proposition`, `consensus-stance-<code>`, `consensus-reason-<code>`, `consensus-submit`, `consensus-result-<versionId>` and `consensus-methodology-note`.
6. `CommunityReasonSection` preserves the current feature gate, load/publish/react/report behavior, structured tag policy derived from the existing Decision CaseVersion response schema, optional 300-character text input and moderation receipt semantics.
7. Existing Community Reasons keys remain stable, including `community-reason-section`, `community-reason-tag-<tag>`, `community-reason-text`, `community-reason-publish` and `community-reason-receipt`.
8. Published Community Reason items remain presentation of the existing snapshot only. This slice must not add author identity, social graph, follower count, popularity/ranking score, recommendation, inferred stance or account/profile linkage.
9. Loading treatment for both surfaces must be deterministic/non-continuous. Submitting state may communicate disabled/in-progress status through iconography/copy without a continuously animating spinner.
10. Existing localized copy is authoritative. This slice introduces no new product claim about consensus validity, representativeness, popularity or user identity.
11. Presentation must use existing `KefeSurface` / `KefeVisualTheme` semantic roles, support light/dark parity, TR/EN, text scaling, screen readers and accessible tap targets, and remove direct dark-only token dependencies from governed Consensus presentation.
12. No backend/API/schema, moderation policy, reaction/report policy, route architecture, feature-mode or persistence change is authorized.
13. Commit First, Blind First, immutable CaseVersion, case-agnostic generic runtime, preview/production isolation and My KEFE observed/descriptive-only boundaries remain unchanged.

## Visual direction

- Consensus should read as a deliberate civic participation instrument, not a generic survey card.
- The participation state should clearly separate integrity/methodology framing, proposition, stance selection, optional reason tags and submit action.
- The participated state should make the user’s selected stance legible without implying correctness or social desirability.
- Aggregate bars remain factual display of the existing aggregate only; no decorative pseudo-precision or new metric is introduced.
- Community Reasons should read as a moderated public-reason surface: privacy/moderation context first, structured tags second, optional text third, publication action fourth.
- Published items should have restrained hierarchy for tags, optional text, reactions and report action while preserving neutrality.
- Loading/error/receipt states should share the same premium semantic vocabulary and avoid decorative continuous animation.

## Acceptance

One exact candidate SHA must prove:

- Consensus remains hidden/empty exactly where current controller state requires and stays bound to the active committed session/CaseVersion;
- Consensus submit/retry behavior and stable interaction keys remain intact;
- no new consensus metric, ranking, recommendation or inference is introduced;
- existing aggregate/provenance values remain display-only and unchanged;
- Community Reasons remains feature-gated and preserves load/publish/react/report behavior, CaseVersion tag policy, optional text limit and moderation receipt semantics;
- no new author identity, social graph, ranking, recommendation, profile linkage or inferred stance is introduced;
- governed presentation uses semantic KEFE surfaces and contains no direct `KefeColorTokens.surfaceElevatedDark`, `borderDark` or `textMutedDark` dependencies;
- loading/submitting treatments are deterministic/non-continuous;
- TR/EN and light/dark render coverage passes with text scaling/accessibility expectations;
- existing production copy boundary, phone acceptance, Commit First/Blind First and mobile regressions remain green;
- API CI, Mobile CI, MVP Beta Gates and Global Readiness succeed on the same candidate SHA.

## Out of scope

New community distribution, social graph/following, author identity, popularity/ranking, reputation, personalization, recommendation, new consensus methodology, new aggregate metrics, backend/API/schema changes, moderation-policy changes, Signal/Impact, profiling/inference, production/store readiness, provider evidence, deployed SLO/operator rollback evidence and human usability claims are not authorized by this ADR.
