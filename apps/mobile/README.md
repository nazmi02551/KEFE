# KEFE Mobile

Flutter consumer application. The client consumes semantic copy/configuration, shared contracts and design tokens; screen code must not duplicate product constants or vendor-specific integrations.

## Current M0 slice

The executable first-use path is:

`Welcome → First Case → Context → Typed Weigh → Private Reason → Commit → Reveal → Perspective → Continue as Guest → Explore`

The regular product path is:

`Explore → Case → Context → Typed Weigh → Private Reason → Commit → Reveal → Perspective`

A Case can also be opened directly through `/case/:caseId` without forcing first-use onboarding.

### First-use onboarding

Onboarding intentionally avoids a long tutorial. A fresh installation sees two concise product-promise steps, then enters the existing low-risk demo Case. The onboarding completion flag is persisted when the user reaches the first Reveal, so an app restart does not force a completed user through the tutorial again. Perspective remains the post-Reveal continuation in the same Case journey; the visible guest-continuation action then advances into Explore.

The current slice does **not** implement account creation and does not encode a final primary-navigation redesign.

### Pre-Commit Context and Sources

The Case screen loads Context through the immutable CaseVersion identifier before Weigh. `ESSENTIAL` blocks are visible by default; `DETAIL` blocks and source metadata require explicit expansion. Claim status (`VERIFIED`, `CLAIMED`, `DISPUTED`, `UNKNOWN`) is displayed separately from source kind.

The Context surface is public/read-only and contains no community result, Perspective, participant reason or other post-Commit signal. Clients preserve editorial order, do not locally re-rank evidence and never embed untrusted remote HTML. Context failure does not unlock result data or destroy the user's decision draft.

### Typed question engine

Case screens no longer own one hard-coded input. Each Question carries `responseType`, requiredness and a response schema. The client dispatches to a question input renderer while the backend remains the authority for response validation.

Currently supported renderers:

- `SINGLE_CHOICE`
- `CONFIDENCE`, using schema-driven `min`, `max` and `step`

Required-question completeness controls Commit. Optional Confidence can be captured without becoming a universal blocker. Unsupported required types do not silently unlock Commit.

### Private Reason Capture

A published CaseVersion can expose an optional `reason` policy inside its question schema. The mobile client renders that policy rather than hard-coding a universal reason form.

The policy can define structured reason tags, tag limits, optional short text and its length limit. Reason data is persisted with the same CaseVersion-pinned local draft as the typed responses. Before Commit, the client synchronizes responses and the optional private reason to the same server-side weigh session.

Reason visibility remains private in this slice. A short-text reason can be marked as pending moderation for the viewer, but that status never means the reason is exposed as Perspective content.

### Post-Reveal Perspective

Perspective is loaded automatically only after a successful Reveal and is rendered below Reveal in the same Case journey. It does not add a primary navigation destination.

The mobile client:

- consumes the actor-owned session-scoped Perspective endpoint
- renders at most four API-ordered roles: `NEAR`, `OPPOSING`, `BRIDGE`, `ALTERNATIVE_CONTEXT`
- does not locally re-rank cards
- distinguishes curated fallback and provenance/methodology metadata
- treats an empty Perspective set as valid
- never derives cards from the local private reason
- never adds reactions, public authoring, popularity metrics or AI summaries in this slice

Perspective transport state is separate from decision recovery: `IDLE`, `LOADING`, `READY`, `CLUSTER_PENDING`, `DEGRADED_CURATED`, `ERROR_RETRYABLE`. A Perspective retry performs only the Perspective GET; it cannot replay answers, private reason writes, Commit or Reveal.

### Architecture

- Riverpod for feature/application state
- GoRouter for declarative routes and Case deep links
- provider-neutral `DecisionRepository` plus optional `ContextRepository` and `PerspectiveRepository` read capabilities
- local `OnboardingStore` boundary for first-use completion state
- HTTP adapter isolated from UI/application state
- schema-driven question and private-reason inputs
- semantic Turkish/English copy catalog
- Light/Dark/System theme support
- Commit First enforced by the backend and reflected in the UI
- accessible controls and semantic selection/status state
- platform secure storage for the guest session token
- per-Case local decision drafts for connectivity recovery

### Runtime configuration

Runtime values are supplied without hard-coded environment URLs:

```bash
flutter run \
  --dart-define=KEFE_API_BASE_URL=http://localhost:8000 \
  --dart-define=KEFE_HTTP_TIMEOUT_SECONDS=12
```

Android emulators typically need `http://10.0.2.2:8000` for a backend running on the host machine.

### Decision recovery

The local draft keeps the pinned CaseVersion, server session ID, typed response map, optional private reason, commit idempotency key and recovery phase.

The recovery state machine is deliberately split into four phases:

1. `editing` — responses/reason exist only as an editable local draft.
2. `syncPending` — the intended decision is frozen locally; responses and reason still need to be synchronized to the server. Commit has **not** been attempted, so retry may safely replay those draft writes.
3. `commitPending` — pre-Commit synchronization completed and the stable idempotency key is durable. Commit may already have reached the server, so retry sends **only Commit with the same key**; it does not replay mutable response/reason writes.
4. `committedAwaitingReveal` — Commit is server-confirmed; only Reveal is retried.

Perspective starts only after Reveal succeeds and therefore sits outside this mutable decision recovery state machine.

### Quality gate

Mobile CI pins Flutter 3.44.4 and runs dependency resolution, formatting, static analysis and widget tests. Tests cover Commit First, Context progressive disclosure and leakage boundaries, ThemeMode.system, local draft restoration, pre-Commit sync recovery, same-key uncertain-Commit recovery without replaying answers/reasons, Reveal-only retry, Explore navigation, direct Case deep links, first-use onboarding, schema-driven Choice/Confidence inputs, private Reason Capture, Perspective Commit gating, bounded role rendering, private-reason non-leakage and Perspective-only retry.
