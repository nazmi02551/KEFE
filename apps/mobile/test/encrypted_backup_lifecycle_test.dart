import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/encrypted_backup_lifecycle_models.dart';

void main() {
  group('E2E Encrypted Backup & Key Ceremony (CAP-086)', () {
    test('ADR-0216 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0216-encrypted-backup-lifecycle.md');
      final contract = File('../../docs/contracts/encrypted-backup-lifecycle.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-ENC-BACKUP-001'));
      expect(contract.readAsStringSync(), contains('ENCRYPTED_VAULT_SYNCED'));
    });

    test('EncryptedBackupModel instantiates properly', () {
      const model = EncryptedBackupModel(
        backupId: 'bkp_1',
        vaultIdentityHash: 'a1b2c3d4e5f67890abcdef1234567890',
        status: EncryptedBackupStatusModel.encryptedVaultSynced,
        encryptedPayloadBytes: 65536,
        keyDerivationAlgorithm: KeyDerivationAlgorithmModel.argon2idAes256Gcm,
        integrityDigest: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
      );

      expect(model.encryptedPayloadBytes, 65536);
      expect(model.status, EncryptedBackupStatusModel.encryptedVaultSynced);
    });

    test('InternalAlphaStrings contains Encrypted Backup localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.encBkpEyebrow, contains('UÇTAN UCA ŞİFRELİ'));
      expect(tr.encBkpStSynced, contains('Şifreli Kasaya'));

      const en = KefeStrings(Locale('en'));
      expect(en.encBkpEyebrow, contains('E2E ENCRYPTED'));
      expect(en.encBkpStSynced, contains('Encrypted Vault'));
    });
  });
}
