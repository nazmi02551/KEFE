# ADR-0018 — Versioned content configuration and review policy

**Status:** Accepted  
**Date:** 2026-07-28

## Context

KEFE authoring already validates Base Format, Domain, Risk, Claim State, response schema and modifier compatibility through a provider-neutral registry. The current bootstrap registry is hard-coded in application code. That is acceptable for the foundation but not for an editorial system that must evolve taxonomy, compatibility and review requirements without application redeploys or silent policy drift.

The approved product model requires Domain → Topic → Base Format → Modifier configuration to be data-driven. Source verification, claim status, content risk and Civic review behavior must remain explicit, auditable and reproducible for the CaseVersion that was approved and published.

## Decision

- Content configuration is a versioned, immutable publication artifact identified by a stable `config_version_id` and monotonic version number.
- Mutable work happens only in `DRAFT` configuration versions. Published configuration versions are immutable.
- At most one configuration version is `PUBLISHED` at a time. Publication supersedes the previous published version atomically.
- Rollback never mutates history. It creates a new DRAFT cloned from an earlier published version, which must be explicitly published after validation.
- Stable IDs are used for Domains, Topics, Base Formats and Modifiers. Display labels are mutable configuration data and never primary identifiers.
- Topics reference a Domain stable ID. Cases continue to require one primary Domain; Topic assignment remains optional until the authoring aggregate owns topic IDs explicitly.
- Modifier compatibility is declared per Base Format in configuration, not in UI code or enums.
- Claim states, source kinds and disclosure levels are configuration-controlled allow-lists used by publication validation.
- Review requirements are derived server-side from content facts and risk attributes. Clients may display the derived requirements but cannot weaken or replace them.
- Initial review modes are `EDITORIAL`, `SOURCE_VERIFICATION`, `RISK_REVIEW` and `CIVIC_REVIEW`.
- Fact-bearing or real-event content requires `SOURCE_VERIFICATION`.
- `L2` and `L3` content requires `RISK_REVIEW`.
- `CIVIC_POLITICS` content or the `CIVIC_INTEGRITY` modifier requires `CIVIC_REVIEW`.
- `L3` content additionally requires `EDITORIAL` review and cannot be published unless all derived review requirements are complete.
- Published CaseVersion validation records the effective configuration version used for the validation decision in audit metadata; consumer content remains independent of a live mutable registry after publication.
- Admin configuration commands require `TAXONOMY_MANAGE`. Existing Admin session, MFA, CSRF and server-derived audit identity rules apply unchanged.
- This ADR does not select a CMS vendor or external configuration service. Persistence is implemented behind ports/adapters.

## Consequences

- Taxonomy and compatibility changes no longer require code edits or enum migrations.
- Historical publication decisions can be reproduced against the effective configuration version.
- A mistaken configuration can be rolled back without rewriting audit history.
- Editorial clients cannot bypass source/risk/Civic review by omitting `required_review_modes` in request bodies.
- The existing hard-coded bootstrap registry becomes seed/default data, not the long-term runtime authority.
