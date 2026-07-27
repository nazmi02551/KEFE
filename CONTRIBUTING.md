# Contributing to KEFE

## Core rules

1. Domain/application code must not import vendor SDKs directly.
2. Published CaseVersion records are immutable.
3. Reveal must never become available before a server-confirmed commit.
4. User-facing copy uses semantic keys; business logic never depends on display strings.
5. Configuration is typed, validated, versioned and auditable; domain invariants are not remote config.
6. Cross-module writes go through declared application ports/services.
7. API/event/schema changes require backward-compatibility review.
8. Secrets never enter source control.

## Workflow

- Branch from `main`.
- Keep changes vertical and reviewable.
- Add or adjust tests with behavior changes.
- Update relevant contracts and ADRs when architecture or public contracts change.
- Prefer squash merge for feature/bootstrap PRs unless history preservation is useful.
