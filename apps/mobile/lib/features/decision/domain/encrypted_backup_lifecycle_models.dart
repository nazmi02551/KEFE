import 'package:flutter/foundation.dart';

enum EncryptedBackupStatusModel {
  backupStaged,
  encryptedVaultSynced,
  restoreVerified,
}

enum KeyDerivationAlgorithmModel {
  argon2idAes256Gcm,
  pbkdf2HmacSha512,
}

@immutable
class EncryptedBackupModel {
  const EncryptedBackupModel({
    required this.backupId,
    required this.vaultIdentityHash,
    required this.status,
    required this.encryptedPayloadBytes,
    required this.keyDerivationAlgorithm,
    required this.integrityDigest,
  });

  final String backupId;
  final String vaultIdentityHash;
  final EncryptedBackupStatusModel status;
  final int encryptedPayloadBytes;
  final KeyDerivationAlgorithmModel keyDerivationAlgorithm;
  final String integrityDigest;
}
