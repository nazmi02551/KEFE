# KEFE Mobile

Flutter consumer application. The client consumes semantic copy/configuration, shared contracts and design tokens; screen code must not duplicate product constants or vendor-specific integrations.

## M0 mobile foundation

The first executable mobile slice implements:

`Guest Identity → Case → Weigh → Commit → Reveal`

### Architecture

- Riverpod for predictable feature/application state
- GoRouter for declarative navigation and future deep links
- provider-neutral `DecisionRepository`
- HTTP adapter isolated from UI/application state
- semantic Turkish/English copy catalog
- Light/Dark/System theme support
- Commit First enforced by the backend and reflected in the UI
- accessible controls, semantic selection state and reduced layout complexity

### Runtime configuration

The API endpoint is supplied without hard-coding environment URLs:

```bash
flutter run \
  --dart-define=KEFE_API_BASE_URL=http://localhost:8000
```

Android emulators typically need `http://10.0.2.2:8000` for a backend running on the host machine.

### Credential storage

The foundation intentionally exposes a `CredentialStore` port. The current memory adapter proves the flow but is not production persistence. A platform secure-storage adapter is required before public beta; raw bearer credentials must never be written to logs, analytics or ordinary preferences.

### Quality gate

Mobile CI pins Flutter 3.44.4 and runs dependency resolution, formatting, static analysis and widget tests. The initial tests verify Commit First and ThemeMode.system behavior.
