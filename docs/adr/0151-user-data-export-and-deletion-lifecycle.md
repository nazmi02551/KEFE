# ADR-0151: User Data Export and Cryptographic Erasure Lifecycle (CAP-085)

## Status

ACCEPTED

## Context

Under KVKK, GDPR, and KEFE's Privacy-First Constitutional Baseline, all users (both registered account holders and guest actors) possess unconditional rights to:
1. Export a machine-readable, verifiable copy of all personal decision drafts, reasons, reactions, and bookmarks.
2. Irrevocably delete all private data attached to their actor identity.

## Decision

1. **Governed Export Bundle**:
   - Includes full dataset manifest, dataset record counts, and canonical SHA-256 integrity checksum.
   - Excludes security tokens, hashes, other users' data, and system-internal operational records.
2. **Cryptographic Erasure & Anonymization Receipt**:
   - Deletion requires explicit `X-KEFE-Delete-Confirm: true` header to prevent accidental data destruction.
   - Private reasons and session links are cryptographically erased.
   - Historical aggregate contributions already committed to published `RevealSnapshot` distributions are permanently anonymized to prevent retroactively corrupting collective statistical integrity.
3. **Traceable Deletion Receipt**:
   - The user receives an immutable `PrivacyDeletionReceipt` confirming `private_data_deleted: true` and `aggregate_contributions_anonymized: true`.

## Consequences

- Full regulatory and constitutional privacy compliance.
- Guarantees zero residual private identifier storage after erasure.
