# ADR-0018 — Versioned content configuration registry

**Status:** Accepted  
**Date:** 2026-07-28

## Context

KEFE's product taxonomy and publication rules are data-driven. Domain, base-format, modifier compatibility, risk class, claim state and required review-mode definitions must evolve without application enum migrations or ad-hoc hard-coded edits. The current authoring validator has a provider-neutral registry port, but the default runtime registry is bootstrapped from in-process constants.

The Content/Admin milestone now provides a secured Admin application boundary, durable Admin principals/sessions and immutable publication workflow. The next coherent step is to make product configuration a separately versioned and audited publication object rather than mutable runtime constants.

## Decision

- Content configuration is a **versioned configuration snapshot**, independent from Case/CaseVersion lifecycle.
- A snapshot contains stable codes and policy relationships for:
  - domains;
  - base formats;
  - modifiers and base-format compatibility;
  - content-risk classes;
  - claim states;
  - required review modes by risk/policy condition.
- Configuration lifecycle is `DRAFT → PUBLISHED → SUPERSEDED`.
- A published configuration snapshot is immutable.
- Publishing a new snapshot atomically supersedes the previous published snapshot; rollback is performed by publishing a new snapshot derived from an older snapshot, never by mutating history.
- Content publication validation resolves exactly one active published configuration snapshot. If no valid published snapshot exists, publication fails closed.
- Stable codes are product identifiers. Display labels/localization are separate presentation data and are not authorization or domain identifiers.
- Configuration mutation and publication are Admin-only and require `TAXONOMY_MANAGE` capability through the existing Admin security boundary.
- Browser mutation requests inherit opaque Admin session + same-session CSRF controls. Client-supplied audit identity is forbidden.
- Configuration persistence is accessed through ports; PostgreSQL is the first adapter and no database library may enter content-authoring domain rules.
- Configuration publication produces an append-only audit entry containing server-derived Admin actor identity and the superseded snapshot, if any.
- The authoring service consumes configuration through `ContentAuthoringRegistry`; callers are not coupled to configuration storage or versioning details.

## Validation rules

A configuration snapshot cannot publish unless:

- codes are non-empty, unique and canonical uppercase identifiers;
- every modifier compatibility reference points to a declared base format and modifier;
- all review-mode mappings point to declared risk classes;
- baseline response types required by the current executable question engine remain representable;
- at least one domain, base format, risk and claim state exist;
- the snapshot remains compatible with binding product rules such as Commit First and immutable CaseVersion semantics.

## Consequences

- Taxonomy and compatibility changes no longer require code migrations when they stay within existing engine capabilities.
- Historical CaseVersions remain interpretable because their stable codes and the configuration snapshot used at publication can be audited.
- A bad configuration can be corrected by a new publication while retaining the exact historical state.
- The Admin UI/API may safely expose configuration management without becoming a CMS/vendor dependency.
- Source verification, claim review and Civic/risk review workflows can build on the same versioned policy substrate in later slices.
