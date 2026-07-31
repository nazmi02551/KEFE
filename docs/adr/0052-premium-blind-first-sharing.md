# ADR-0052 — Premium Blind First sharing visual slice 14

- Status: Accepted
- Date: 2026-07-31
- Issue: #123
- Stack base: PR #122 cleanup/status head `aeae083a640c3c658d1a0536e3f17d853540d982`
- Inherited verified Slice 13 runtime: `49ee321925d7e54948376f1990e08eceaf41881b`
- Extends: ADR-0038, ADR-0039, ADR-0051

## Context

The existing sharing runtime already has the correct safety shape but remains visually behind the rest of the premium mobile experience.

There are two ends to one sharing journey:

1. `ShareSection` creates, copies and revokes a share link from an already-owned decision session.
2. `PublicShareScreen` resolves the share token and lets the receiver enter the Case flow.

The current product contract is explicitly case-only and Blind First:

- sharing is feature-gated by `shareExperienceEnabledProvider`;
- `ShareController.create()` passes `includeDecision: false` to the repository;
- `PreviewShareRepository.create()` rejects `includeDecision == true` with `SHARE_DECISION_EXPOSURE_NOT_SUPPORTED`;
- `PublicShare` contains Case/CaseVersion identity and presentation content but no sender decision, confidence, private reason, Reveal/community result, expert result or personal history;
- the receiver goes to `/case/:caseId`, where existing Commit First / Blind First behavior remains authoritative;
- existing phone acceptance asserts that the inbound share surface and the receiver Case contain no `reveal-card` before receiver Commit.

The presentation itself is still generic: bare Card/SelectableText outbound, generic AppBar/loading/error/Chip hierarchy inbound.

Community presentation is not part of this ADR. Adding community semantics or read models would be a separate product boundary decision.

## Decision

1. Outbound and inbound sharing are one premium visual slice because both are governed by the same case-only Blind First contract.
2. `shareExperienceEnabledProvider` remains authoritative. Disabled sharing remains absent and this slice must not enable it in production or preview by default.
3. Outbound sharing preserves the exact controller and repository behavior, including `includeDecision: false`, existing create/copy/revoke actions, token format and deep link format `kefe:///share/<token>`.
4. Existing outbound widget keys remain stable: `share-section`, `share-create`, `share-deep-link`, `share-copy`, `share-revoke`, `share-error`.
5. Inbound sharing preserves token resolution through `shareRepositoryProvider.read(token)` and the route from `public-share-weigh` to `/case/<caseId>`.
6. Existing inbound keys remain stable: `public-share-error`, `public-share-title`, `public-share-weigh`.
7. The inbound surface may render only case-only share content already present in `PublicShare`: title, summary, primary domain and non-sensitive share identity metadata needed for presentation. It must not add sender decision, sender confidence, sender reason, Reveal/community distribution, expert result, consensus, account/profile, activity/history or any post-Commit derived value.
8. The outbound ready state may visually emphasize that the created link is case-only, but it may not imply that sender judgment or result is embedded in the link.
9. Existing localized copy is authoritative. No new product semantics are introduced by this slice.
10. Loading treatment must be deterministic/non-continuous so shared/offstage tests can settle. Error/retry remains descriptive of existing transport/API state.
11. The premium surface system must use existing `KefeVisualTheme` / `KefeSurface` semantic roles and support light/dark parity, TR/EN, text scaling, screen readers and accessible tap targets.
12. No backend/API/share schema or route architecture change is authorized.
13. Commit First, Blind First, immutable CaseVersion, case-agnostic generic runtime, preview/production isolation and My KEFE observed/descriptive-only boundaries remain unchanged.

## Visual direction

- outbound sharing reads as a restrained trust surface rather than a generic utility Card;
- create state highlights the case-only sharing promise before action;
- ready state gives the deep link a stable readable surface with clear copy and revoke actions;
- inbound share begins with a recognizable KEFE identity, clear shared-Case hierarchy and Blind First CTA;
- loading/error/ready use the same premium surface vocabulary without decorative continuous animation;
- gold remains the primary KEFE accent, while domain treatment uses existing semantic framing rather than invented category colors.

## Acceptance

One exact candidate SHA must prove:

- outbound sharing remains hidden when feature-gated off and preserves all existing create/copy/revoke keys and controller calls when enabled;
- `ShareController.create()` still sends `includeDecision: false`;
- preview sharing still rejects decision exposure requests;
- inbound sharing renders in TR/EN and light/dark without overflow and preserves existing title/error/weigh keys;
- inbound CTA still routes to `/case/:caseId`;
- no `reveal-card` or sender decision/result data is exposed on the inbound share surface or receiver Case before receiver Commit;
- `PublicShare` schema remains case-only and does not grow sender decision/confidence/reason/result/history fields;
- governed sharing presentation uses semantic KEFE surfaces and does not depend on direct `KefeColorTokens.surfaceDark`, `borderDark` or `textMutedDark` values;
- existing production copy boundary, phone acceptance, Commit First/Blind First and share regressions remain green;
- API CI, Mobile CI, MVP Beta Gates and Global Readiness succeed on the same candidate SHA.

## Out of scope

Community/consensus product work, share backend/API/schema changes, sender decision exposure, provider/distribution integrations, social-network SDKs, analytics attribution, profiling/inference, Signal/Impact, production/store readiness, deployed SLO evidence and human usability claims are not authorized by this ADR.
