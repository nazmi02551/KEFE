from __future__ import annotations

from kefe_api.modules.decision.encrypted_backup_lifecycle import (
    EncryptedBackupLifecycleService,
    EncryptedBackupResult,
    EncryptedBackupStatus,
    KeyDerivationAlgorithm,
)


def test_encrypted_backup_registers_validly() -> None:
    r = EncryptedBackupLifecycleService.register_backup(
        backup_id="bkp_001",
        vault_identity_hash="a1b2c3d4e5f67890abcdef1234567890",
        status=EncryptedBackupStatus.ENCRYPTED_VAULT_SYNCED,
        encrypted_payload_bytes=65536,
        key_derivation_algorithm=KeyDerivationAlgorithm.ARGON2ID_AES_256_GCM,
        integrity_digest="9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
    )

    assert isinstance(r, EncryptedBackupResult)
    assert r.status == EncryptedBackupStatus.ENCRYPTED_VAULT_SYNCED
    assert r.encrypted_payload_bytes == 65536
    assert r.key_derivation_algorithm == KeyDerivationAlgorithm.ARGON2ID_AES_256_GCM


def test_encrypted_backup_invalid_bytes() -> None:
    failed = False
    try:
        EncryptedBackupLifecycleService.register_backup(
            backup_id="bkp_002",
            vault_identity_hash="short_hash",  # < 16
            status=EncryptedBackupStatus.BACKUP_STAGED,
            encrypted_payload_bytes=0,  # <= 0
            key_derivation_algorithm=KeyDerivationAlgorithm.PBKDF2_HMAC_SHA512,
            integrity_digest="short_digest",  # < 32
        )
    except ValueError:
        failed = True

    assert failed is True
