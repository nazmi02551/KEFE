# ADR-0216: End-to-End Encrypted Backup & Key Lifecycle (CAP-086)

## Status

ACCEPTED

## Context

User weighing histories, private reflections, and draft queues must remain completely under the user's sovereign cryptographic control. Under `KEFE-PB-001`, `KEFE-ETG-001`, and `KEFE-ENG-001`, KEFE supports client-side zero-knowledge encrypted backups secured with Argon2id + AES-256-GCM.

## Decision

1. **Backup State Taxonomy**:
   - `BACKUP_STAGED`: Prepared locally prior to remote vault sync.
   - `ENCRYPTED_VAULT_SYNCED`: Successfully encrypted and stored in sovereign storage.
   - `RESTORE_VERIFIED`: Decrypted and integrity-verified on secondary device.
2. **Cryptographic Invariant**:
   - Zero plaintext user reflections or keys transmitted to KEFE servers.

## Consequences

- Prevents data leakage even under compromised cloud storage.
- Ensures seamless cross-device portability with mathematical zero-knowledge privacy.
