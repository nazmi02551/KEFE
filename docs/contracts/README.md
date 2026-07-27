# Machine-readable contracts

This directory contains implementation contracts derived from the approved KEFE documentation baseline.

Contract changes must be reviewed for compatibility and synchronized with the relevant normative document and decision history.

`manifest.v1.yaml` is the current machine-readable registry. Versioned contract files remain in the repository for traceability; the manifest identifies which version is active.

Key contract families:

- OpenAPI / HTTP API contracts
- PostgreSQL physical schema baseline
- domain/analytics event envelopes and payloads
- typed configuration registry
- error code registry
- core ERD
- repository/package boundary contract

For M0, Alembic migrations are the executable database source of truth. The versioned PostgreSQL schema file is a reviewed snapshot derived from those migrations. CI fitness checks fail if declared contract paths disappear or required persistence/outbox invariants drift.
