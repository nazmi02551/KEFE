# KEFE Mobile

Flutter consumer application. The client consumes semantic copy/configuration, shared contracts and design tokens; screen code must not duplicate product constants or vendor-specific integrations.

## Current M0 slice

The executable first-use path is:

`Welcome → First Case → Weigh → Commit → Reveal → Continue as Guest → Explore`

The regular product path is:

`Explore → Case → Weigh → Commit → Reveal`

A Case can also be opened directly through `/case/:caseId` without forcing first-use onboarding.

### First-use onboarding

Onboarding intentionally avoids a long tutorial. A fresh installation sees two concise product-promise steps, then enters the existing low-risk demo Case. The onboarding completion flag is written only after the user reaches Reveal and chooses to continue as a guest. This demonstrates the product value before asking for any future account upgrade.

The current slice does **not** implement account creation and does not encode a final 3-vs-4-tab navigation decision.

### Architecture

- Riverpod for feature/application state
- GoRouter for declarative routes and Case deep links
- provider-neutral `DecisionRepository`
- local `OnboardingStore` boundary for first-use completion state
- HTTP adapter isolated from UI/application state
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

The local draft keeps the pinned CaseVersion, server session ID, selected response and commit recovery state. Before the first commit request, the client persists the idempotency key. When network outcome is uncertain, the same key is reused; after Commit is confirmed, only Reveal is retried.

Drafts are keyed by Case ID, so opening another Case cannot silently replace a different in-progress draft.

### Quality gate

Mobile CI pins Flutter 3.44.4 and runs dependency resolution, formatting, static analysis and widget tests. Tests cover Commit First, ThemeMode.system, local draft restoration, uncertain-commit recovery, Reveal-only retry, Explore navigation, direct Case deep links and the first-use onboarding path through Reveal.
