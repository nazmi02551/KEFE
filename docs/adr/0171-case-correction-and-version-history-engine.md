# ADR-0171: Case Correction and Version History Engine (CAP-072)

## Status

ACCEPTED

## Context

In accordance with `KEFE-GOV-001` (Dokümantasyon Yönetişimi) and `KEFE-TIM-001` (Trust & Integrity), when published cases are updated with new factual developments or typo corrections, silent modifications are strictly forbidden. An immutable, publicly readable audit trail of corrections must be maintained for every case version.

## Decision

1. **Structured Correction Record**:
   - `correction_id`, `case_version_id`, `correction_type` (`FACTUAL_UPDATE`, `CLARIFICATION`, `SOURCE_EXPANSION`, `TYPO_FIX`, `LEGAL_STATUS_UPDATE`), `severity` (`MINOR`, `MATERIAL`, `SUBSTANTIAL`), `timestamp`, `summary`, `editorial_rationale`, `previous_text`, `corrected_text`.
2. **Immutable Append-Only Log**:
   - Correction records cannot be edited or erased once published.

## Consequences

- Full journalistic transparency and public accountability.
- Fulfills the governance and audit requirements of the KEFE constitution.
