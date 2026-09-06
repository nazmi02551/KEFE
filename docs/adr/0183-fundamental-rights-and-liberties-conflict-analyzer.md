# ADR-0183: Fundamental Rights and Liberties Conflict Analyzer (CAP-024)

## Status

ACCEPTED

## Context

Hard civic dilemmas often involve tragic choices where legitimate constitutional rights collide (e.g., public health lockdowns vs freedom of movement, digital privacy vs terror prevention). Under `KEFE-CQB-001` (Content & Question Design Bible) and `KEFE-PB-001` (Product Bible), the platform must systematically audit and map rights collisions.

## Decision

1. **Collision Taxonomy**:
   - `PRIVACY_VS_SECURITY`
   - `EXPRESSION_VS_DIGNITY`
   - `PROPERTY_VS_ENVIRONMENT`
   - `INDIVIDUAL_LIBERTY_VS_PUBLIC_HEALTH`
2. **Inalienable Core Assessment**:
   - Classifies restriction severity into `PERMISSIBLE_RESTRICTION`, `CORE_RIGHT_EROSION`, and `UNCONSTITUTIONAL_BREACH`.

## Consequences

- Formulates rights collisions in structured constitutional jurisprudence terms.
- Eliminates naive zero-sum framing.
