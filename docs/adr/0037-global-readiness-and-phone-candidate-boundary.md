# ADR-0037 — Global readiness and phone candidate boundary

Status: Proposed for implementation
Date: 2026-07-30

## Context

KEFE is global-first. Localization is not only UI translation: a published CaseVersion must be able to declare language/terminology, cultural context, legal context and market scope without creating Case-specific runtime classes. The mobile app also needs explicit user-selectable language/theme preferences and a phone-test build that is functional without pretending an unavailable production backend exists.

The previous `MVP Beta Gates` production-entry APK intentionally used an invalid API origin to prove fail-closed production/preview isolation. That artifact is engineering evidence, not a phone-test candidate.

## Decision

1. Keep production and Product Preview isolated. `lib/main.dart` never falls back to preview fixtures when the API is unavailable.
2. Introduce a separately named internal phone candidate from `lib/main_preview.dart`. It must be visibly attributable as Product Preview/internal test evidence and must never be called production/store-ready.
3. App presentation preferences are user-owned and device-local:
   - locale mode: SYSTEM or an explicitly supported locale;
   - theme mode: SYSTEM, LIGHT or DARK;
   - preferences persist locally and may be changed without Account creation.
4. UI strings must come from the localization boundary. Direct user-facing literals outside localization/preview fixture boundaries are rejected by an automated hardcode gate.
5. Published CaseVersion global metadata is immutable with the CaseVersion and includes:
   - `content_locale` as a normalized BCP-47-like language tag;
   - `market_scope`: GLOBAL or COUNTRY_SET;
   - bounded ISO-3166 alpha-2 `country_codes` when COUNTRY_SET;
   - optional `cultural_context_note` and `legal_context_note` as editorial content, not runtime inference.
6. Discovery filtering is locale/country aware but generic. Global content may coexist with country-scoped content; selection must not profile ideology or infer sensitive traits.
7. My KEFE remains observed/descriptive history only.
8. No country-specific Screen/Controller/Service classes are permitted.

## Consequences

- Existing CaseVersion identity/version immutability remains intact.
- Translation/localization becomes explicit metadata and authoring responsibility rather than runtime text substitution for editorial content.
- Adding new locales/countries is configuration/content work plus translation, not a new product runtime branch.
- A phone-test candidate can be installed and exercised without weakening production fail-closed behavior.

## Non-goals

- No production backend deployment is claimed by this ADR.
- No automatic machine translation is introduced.
- No geopolitical/legal truth inference is performed by the client.
- No public release/store readiness is implied.