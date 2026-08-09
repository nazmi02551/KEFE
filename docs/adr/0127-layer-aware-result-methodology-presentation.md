# ADR-0127 — Layer-aware Result methodology presentation

Status: Proposed / F4 candidate

Issue: #354

Parent: PR #352 / `6cbf19b9a855bf5531ed74bbf4362696281ebbaf`

## Context

Connected Alpha introduces a live `RAW` Collective Result fallback when a CaseVersion has no reviewed TRUSTED snapshot. The mobile Result card already carries the server-provided result `layer`, but its methodology footer previously ignored that field and always rendered the existing TRUSTED formulation:

`{trustedSample} · n={sampleSize} · {confidence}`

In Turkish, `trustedSample` is `Güvenilir örneklem`; in English it is `Trusted sample`. The existing confidence resolver also had no `INSUFFICIENT` label, so a RAW result could display the backend code directly.

That presentation would turn an intentionally unqualified RAW participation aggregate into a stronger methodology claim than the backend contract allows.

## Decision

Result methodology copy must resolve from the actual `RevealResult.layer`.

### TRUSTED

Keep the existing TRUSTED copy and HIGH/MEDIUM/LOW localization unchanged. This slice does not reinterpret TRUSTED methodology.

### RAW

Use explicit observed-participation language:

- TR: `Gözlenen kaydedilmiş katılım`;
- EN: `Observed committed participation`.

RAW `INSUFFICIENT` is presented as:

- TR: `Güven düzeyi hesaplanmadı`;
- EN: `Confidence not assessed`.

The methodology sentence must also state:

- TR: `Temsiliyet iddiası yok`;
- EN: `No representativeness claim`.

### Unknown future layers

Unknown layers must use a neutral layer label containing the actual layer code and must never silently inherit TRUSTED wording.

## Localization structure

The existing Internal Alpha catalog remains unchanged for TRUSTED copy. A small dedicated Result-methodology catalog owns RAW and generic-layer copy, and a layer-aware resolver delegates TRUSTED back to the existing method. This keeps the change narrow and prevents duplicate TRUSTED strings.

## Presentation boundary

`RevealResultCard` changes only the methodology resolver call. Distribution arithmetic, selected-option treatment, animation, KEFE Gap, semantics, layout and Flow behavior are unchanged.

## Methodology boundary

RAW remains observed committed participation only. This copy does not create statistical confidence, representativeness, Signal, Impact, truth or normative authority.

## Non-claims

This ADR does not qualify a methodology layer, change backend aggregation, implement Signal/Impact, prove human usability, prove store readiness, complete F4 or promote CAP-123.
