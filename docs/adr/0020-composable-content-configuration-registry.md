# ADR-0020 — Composable Content Configuration registry boundary

**Status:** Accepted  
**Date:** 2026-07-28

## Context

ADR-0018 introduced immutable versioned Content Configuration for Domain, Topic, Base Format, Modifier and review-policy inputs. ADR-0019 subsequently established the broader case-agnostic hierarchy `Primitive → Capability → FlowTemplateVersion → CaseVersion` and requires schema-before-screen composition without case-specific runtime types.

The existing ContentConfigurationSnapshot can remain the publication/versioning boundary, but its aggregate is currently too narrow to describe composable Flow semantics. At the same time, expanding it must not prematurely collapse MethodologyVersion, runtime CaseVersion state, or consumer decision history into one configuration document.

## Decision

### Registry ownership

The versioned Content Configuration aggregate owns **authoring/composition registries**:
- existing Domain, Topic, Base Format and Modifier registries,
- Primitive definitions,
- Capability definitions and primitive compatibility,
- FlowTemplateVersion definitions,
- existing publication-validation allow-lists needed by authoring.

Methodology scoring/taxonomy semantics that must evolve independently of editorial composition remain a separate future MethodologyVersion boundary. Published CaseVersion/Result/Signal objects must pin the relevant immutable references when those boundaries are implemented.

### Primitive definition

A Primitive is a stable semantic building block, not a widget class. Initial definition fields are:
- stable `code`,
- `label_key`,
- optional schema reference describing the payload contract,
- enabled state.

Renderer/UI selection is downstream of schema semantics and is not part of the domain identity.

### Capability definition

A Capability is reusable behavior that may be applied to compatible Primitives. Initial definition fields are:
- stable `code`,
- `label_key`,
- compatible Primitive codes,
- optional configuration-schema reference,
- enabled state.

An empty compatibility set means the Capability does not declare a Primitive restriction at this layer; it does not mean every runtime combination is automatically valid forever.

### FlowTemplateVersion definition

A Flow Template is a versioned reusable authoring composition, not a runtime Case subtype. Its stable identity is `(template_code, template_version)`.

The first executable representation contains:
- stable template code and positive version number,
- label key,
- entry step code,
- ordered Step definitions,
- enabled state.

Each Step contains:
- stable step code within the template version,
- one Primitive code,
- zero or more Capability codes,
- optional payload-schema reference,
- zero or more explicit next-step codes.

This model supports multiple outgoing transitions structurally. Conditional transition expression semantics are intentionally deferred; the first implementation stores only explicit target step codes and does not invent a condition DSL.

### Validation invariants

Before a configuration draft can be saved/published:
- Primitive, Capability and Flow Template identities are unique.
- every Capability compatibility reference points to an available Primitive.
- every Flow Step references an available Primitive and available Capabilities.
- when a Capability declares compatible Primitives, a Step may use it only on a compatible Primitive.
- step codes are unique within a FlowTemplateVersion.
- entry step exists.
- all next-step references exist in the same FlowTemplateVersion.
- a template has at least one Step and at least one terminal Step.

Cycle prohibition and conditional-branch DSL are not locked by this ADR.

### Compatibility and migration

- Existing Base Format/Modifier semantics remain supported during migration; they are not reinterpreted as runtime classes.
- Existing published configuration remains immutable.
- Bootstrap configuration gains a generic starter Primitive/Capability/Flow registry without removing current fields.
- This slice does not yet change consumer CaseVersion storage or mobile rendering.
- This slice does not migrate the legacy Context `UNKNOWN` claim status; first-class Claim migration is a separate bounded-context change.

## Consequences

- PR #45's JSONB persistence approach remains compatible in principle because the aggregate document can expand without introducing case-specific tables, but its serialization/schema snapshot must be updated after this domain slice.
- Admin configuration HTTP work should manage the expanded aggregate only after this domain contract is green.
- A following vertical slice can pin a resolved Flow onto AuthoringCaseVersion/consumer CaseVersion and teach one generic renderer/executor path, rather than building a case-specific UI.
