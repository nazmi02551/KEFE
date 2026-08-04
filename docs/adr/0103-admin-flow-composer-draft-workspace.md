# ADR-0103 — Bounded Admin Flow Composer DRAFT Workspace

- **Status:** Accepted for implementation
- **Date:** 2026-08-04
- **Capabilities:** CAP-064 (primary), CAP-063 and CAP-126 (supporting)
- **Parent runtime:** PR #301 exact verified head `f4c11547c0373017c527cfcf0a2d03dd3d3a9d97`

## Context

The active Admin stack now provides a Proposal-to-DRAFT path, a bounded Case Builder and an independent Editorial Quality Review workspace. `ContentConfigurationSnapshot` already owns versioned Primitive, Capability and Flow Template definitions, and publication already pins a resolved Flow/configuration snapshot into immutable published `CaseVersion` data.

The remaining P0 authoring gap is not a second Flow store or a publication shortcut. Editors need a bounded surface for composing generic Flow templates inside an existing DRAFT content-configuration version while preserving all non-Flow configuration fields and the existing publication authority.

The current generic Flow runtime evaluates predecessor satisfaction from the pinned Flow graph. Cyclic or unreachable topology can leave steps permanently blocked, so the authoring boundary must reject those structures before they can enter a published configuration.

## Decision

Implement one additive Flow Composer adapter and one Admin Studio workspace over the existing `ContentConfigurationSnapshot` aggregate.

### Authority and lifecycle

- `ContentConfigurationSnapshot` remains the sole configuration and Flow authority.
- Flow Composer operates only on an exact configuration version in `DRAFT` state.
- The adapter delegates draft creation and saving to the existing secured content-configuration service.
- Published and superseded configuration versions are read-only and cannot be saved through Flow Composer.
- Flow Composer does not publish, supersede or create rollback drafts.
- Saving a Flow draft has no direct consumer-runtime effect; consumer runtime continues to use Flow/configuration data pinned during the separate publication path.

### Read model

The Flow Composer read response includes:

- configuration identity, version, lifecycle state and clone provenance;
- enabled and disabled Primitive definitions;
- enabled and disabled Capability definitions with compatibility metadata;
- all versioned Flow Template definitions and their ordered Steps;
- configuration audit entries for the exact version when explicitly requested.

Primitive and Capability catalogs are reference-only in this workspace. Taxonomies, risks, source kinds, claim states, disclosure levels, modifier compatibility and other non-Flow fields are not client-editable through Flow Composer.

### Write model

The client submits only the replacement `flow_templates` collection for an exact DRAFT configuration version. The server reloads the canonical DRAFT, replaces only `flow_templates` and preserves every non-Flow field server-side before invoking the existing configuration save command.

Every write requires:

- the existing Admin session and `TAXONOMY_MANAGE` capability;
- same-session `X-KEFE-CSRF` verification before the mutation reaches the domain service;
- an exact DRAFT version identity;
- strict request models with unknown fields rejected.

### Flow validation

The existing content-configuration domain validation remains authoritative and is strengthened for Flow graph safety. Each Flow Template version must have:

- a positive version and at least one Step;
- a unique `(flow_code, version_no)` identity in the configuration;
- unique Step codes;
- an existing entry Step;
- at least one terminal Step;
- Primitive and Capability references that exist and obey enabled-state and compatibility rules;
- transitions that reference existing Steps;
- every Step reachable from the entry Step;
- an acyclic topology, including rejection of self-loops.

Flow codes and Step codes remain stable identifiers. Reordering the array does not rewrite those identities.

### Admin Studio

Add `/flow-composer` with:

- no request on mount;
- explicit session entry;
- explicit “create DRAFT from current” command;
- exact-ID load with optional query prefill but no automatic request;
- structured Flow Template and Step forms;
- read-only Primitive and Capability catalogs;
- add/remove/reorder controls without drag-and-drop dependency;
- client-side structural checks before save, while server validation remains authoritative;
- a deterministic text topology preview;
- explicit save and explicit audit load;
- unsaved-change protection;
- no browser persistence of session or CSRF values;
- no publish, rollback, Case editing, review decision or consumer-preview mutation.

## Security and operational boundaries

- Existing Admin identity, capability policy, CSRF verifier and append-only configuration audit remain authoritative.
- Errors are bounded and rendered as text; raw secrets, credentials and backend evidence bodies are not exposed.
- HTTPS remains required outside localhost.
- No autosave, bulk mutation or background synchronization is introduced.
- Preview fixtures are not used as a production fallback.

## Consequences

Positive:

- Generic Flow templates become operable without creating a parallel CMS.
- Flow graph defects fail before configuration publication.
- Non-Flow configuration fields cannot be accidentally overwritten by the bounded client.
- Case Builder can continue to reference stable Flow code/version identities while publication remains separately governed.

Trade-offs:

- The content-configuration validation contract becomes stricter for previously accepted cyclic or unreachable graphs.
- Same-version OpenAPI composition gains another isolated additive overlay.
- The initial composer is structured and accessible but deliberately does not include visual drag-and-drop graph authoring.

## Explicit non-goals

This ADR does not implement configuration publication UI, rollback UI, Case publication, Case review, visual drag-and-drop topology, automatic Flow generation, automated authoring/review/approval, consumer runtime changes, provider activation, production deployment, a release APK, human usability/CQB acceptance, deployed SLO/load/observability, operator rollback validation or store compliance.
