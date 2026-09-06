import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/privacy/data/preview_privacy_repository.dart';

void main() {
  group('User Data Export and Erasure Lifecycle (CAP-085)', () {
    test('ADR-0151 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0151-user-data-export-and-deletion-lifecycle.md');
      final contract = File('../../docs/contracts/user-data-export-and-deletion.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-USER-DATA-EXPORT-DELETION-001'));
      expect(contract.readAsStringSync(), contains('zero_residual_private_identifiers'));
    });

    test('PreviewPrivacyRepository generates valid export and deletion receipts', () async {
      final repo = PreviewPrivacyRepository();

      final exportData = await repo.export();
      expect(exportData, contains('schema_version'));
      expect(exportData, contains('manifest'));

      final receipt = await repo.delete();
      expect(receipt.privateDataDeleted, isTrue);
      expect(receipt.aggregateContributionsAnonymized, isTrue);
    });

    test('InternalAlphaStrings contains privacy copy and delete strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.privacyHeading.toLowerCase(), contains('gizli'));
      expect(tr.privacyExportReady, contains('hazır'));

      const en = KefeStrings(Locale('en'));
      expect(en.privacyHeading.toLowerCase(), contains('privacy'));
      expect(en.privacyExportReady, contains('ready'));
    });
  });
}
