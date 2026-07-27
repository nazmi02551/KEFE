# ADR-0005 — Flutter mobile foundation and client boundaries

**Status:** Accepted  
**Date:** 2026-07-27

## Context

The backend M0 walking skeleton now exposes provider-neutral guest identity and `Case → Weigh → Commit → Reveal` contracts. The first consumer client must preserve KEFE's configuration-driven, localization-first, theme-independent and Commit First principles without coupling screen code to HTTP or credential vendors.

## Decision

- Flutter is the consumer mobile framework.
- Riverpod is the application/feature state standard.
- GoRouter owns declarative navigation and future deep-link handling.
- UI code depends on a `DecisionRepository` port rather than HTTP details.
- API base URLs are runtime configuration supplied through `--dart-define`; environment URLs are not duplicated in screens.
- User-facing copy is addressed through a semantic localization catalog.
- Light, Dark and System are supported through semantic design tokens.
- Guest credentials are obtained through the Identity API and attached as bearer credentials.
- Credential persistence is behind a `CredentialStore` port. The M0 memory adapter is non-production; secure platform storage is mandatory before public beta.
- Reveal is rendered only after server-confirmed commit. Client-side state never overrides the backend Commit First invariant.
- Mobile CI pins a reviewed Flutter stable patch and enforces formatting, analysis and widget tests.

## Consequences

- Secure storage, alternate HTTP clients, analytics and device-integrity providers can be added through adapters without rewriting the decision UI.
- The first mobile package can be tested without generating all platform runner directories.
- Deep links, offline encrypted drafts and account merge remain subsequent slices.
- The dependency versions and pinned Flutter patch must be reviewed by Dependabot/release maintenance rather than silently floating in production.
