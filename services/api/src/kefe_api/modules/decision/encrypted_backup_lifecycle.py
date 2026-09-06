from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class EncryptedBackupStatus(StrEnum):
    BACKUP_STAGED = "BACKUP_STAGED"
    ENCRYPTED_VAULT_SYNCED = "ENCRYPTED_VAULT_SYNCED"
    RESTORE_VERIFIED = "RESTORE_VERIFIED"


class KeyDerivationAlgorithm(StrEnum):
    ARGON2ID_AES_256_GCM = "ARGON2ID_AES_256_GCM"
    PBKDF2_HMAC_SHA512 = "PBKDF2_HMAC_SHA512"


@dataclass(frozen=True, slots=True)
class EncryptedBackupResult:
    backup_id: str
    vault_identity_hash: str
    status: EncryptedBackupStatus
    encrypted_payload_bytes: int
    key_derivation_algorithm: KeyDerivationAlgorithm
    integrity_digest: str


class EncryptedBackupLifecycleService:
    @staticmethod
    def register_backup(
        *,
        backup_id: str,
        vault_identity_hash: str,
        status: EncryptedBackupStatus,
        encrypted_payload_bytes: int,
        key_derivation_algorithm: KeyDerivationAlgorithm,
        integrity_digest: str,
    ) -> EncryptedBackupResult:
        if len(vault_identity_hash.strip()) < 16:
            raise ValueError("vault_identity_hash must have at least 16 characters")
        if encrypted_payload_bytes <= 0:
            raise ValueError(f"encrypted_payload_bytes must be > 0, got {encrypted_payload_bytes}")
        if len(integrity_digest.strip()) < 32:
            raise ValueError("integrity_digest must have at least 32 characters")

        return EncryptedBackupResult(
            backup_id=backup_id.strip(),
            vault_identity_hash=vault_identity_hash.strip(),
            status=status,
            encrypted_payload_bytes=encrypted_payload_bytes,
            key_derivation_algorithm=key_derivation_algorithm,
            integrity_digest=integrity_digest.strip(),
        )
