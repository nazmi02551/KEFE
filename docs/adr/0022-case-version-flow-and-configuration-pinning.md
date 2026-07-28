# ADR-0022 — CaseVersion Flow and Content Configuration Pinning

**Status:** Accepted  
**Date:** 2026-07-28

## Context

ADR-0019 defines KEFE as a case-agnostic decision/public-reasoning engine composed as `Primitive → Capability → FlowTemplateVersion → CaseVersion`. ADR-0020 and PR #47 made Primitive/Capability/FlowTemplateVersion data-driven; PR #49 persisted that configuration durably; PR #51 exposed its secured Admin lifecycle.

A published CaseVersion cannot depend on whatever Content Configuration happens to be live later. Doing so would silently reinterpret historical cases when a Flow Template, Primitive compatibility, Capability semantics or taxonomy changes.

The consumer runtime therefore needs a publication-time, immutable execution description and provenance record before generic Flow execution can be introduced.

## Decision

### Authoring selection

A DRAFT CaseVersion selects a Flow Template by the stable pair:

- `flow_template_code`
- `flow_template_version_no`

This pair is authoring content/configuration metadata, not a runtime Case type.

### Publication-time resolution

At publication, the server resolves the selected Flow against the **current PUBLISHED ContentConfigurationSnapshot** and validates that:

- the selected Domain and Base Format are enabled,
- every Modifier is enabled and compatible with the selected Base Format,
- the selected FlowTemplateVersion exists and is enabled,
- every referenced Primitive and Capability remains enabled and compatible under that published configuration.

Publication fails if the effective published configuration cannot resolve the Case.

### Immutable pin

Successful publication writes these server-derived fields onto the immutable CaseVersion:

- `content_configuration_id`
- `content_configuration_version_no`
- `resolved_flow`

`resolved_flow` is a self-contained immutable snapshot containing:

- template code and version,
- entry Step,
- ordered Step definitions,
- each Step's Primitive,
- Capability references,
- transition targets,
- payload schema reference.

The client cannot submit or override these publication provenance fields.

### Revision semantics

Creating a new DRAFT revision preserves the editorial Flow selection but clears the prior publication pin. The new revision must resolve again against the effective PUBLISHED configuration when it is published.

Published/SUPERSEDED/WITHDRAWN versions keep their original resolved Flow and configuration provenance permanently.

### Consumer materialization

Publication atomically materializes the same provenance into `content.case_version`. Consumer reads and later Flow execution use the CaseVersion-pinned resolved Flow, never live configuration lookup.

### Backward-compatible transition

Existing authoring callers that do not yet choose a Flow explicitly receive the transitional editorial default `STANDARD_COMMIT_REVEAL` version `1`. This default is configuration data, not a Case runtime subclass, and may later be removed once all authoring surfaces select Flow explicitly.

### Methodology provenance

MethodologyVersion pinning remains a separate future slice. ADR-0022 does not fabricate a methodology version before that bounded context exists.

## Consequences

- Historical published Cases are reproducible even after configuration evolution.
- Generic Flow execution can be implemented without consulting live configuration.
- Configuration rollback or new Flow versions do not rewrite existing Case behavior.
- Admin/editorial draft semantics remain flexible while publication remains server-authoritative.
- The next slice can expose a generic consumer Flow read/execution contract using the resolved Flow snapshot.