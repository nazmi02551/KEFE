import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/decision_receipt_models.dart';

void main() {
  group('Versioned Decision Receipt Engine (CAP-012)', () {
    test('ADR-0189 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0189-versioned-decision-receipt.md');
      final contract = File('../../docs/contracts/decision-receipt.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-DECISION-RECEIPT-001'));
    });

    test('DecisionReceiptModel instantiates properly', () {
      const model = DecisionReceiptModel(
        receiptId: 'kefe-rcpt-8f1293a',
        caseVersionId: 'case-1',
        committedChoice: 'SEÇENEK_A',
        integrityDigest: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
        timestampUtc: '2026-09-01T12:00:00Z',
      );

      expect(model.receiptId, 'kefe-rcpt-8f1293a');
      expect(model.committedChoice, 'SEÇENEK_A');
    });

    test('InternalAlphaStrings contains Decision Receipt localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.receiptEyebrow, contains('KRİPTOGRAFİK KARAR'));
      expect(tr.receiptVerifiedBadge, contains('MÜHÜRLENDİ'));

      const en = KefeStrings(Locale('en'));
      expect(en.receiptEyebrow, contains('CRYPTOGRAPHIC DECISION'));
      expect(en.receiptVerifiedBadge, contains('SEALED'));
    });
  });
}
