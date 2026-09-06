import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/public_procurement_oversight_models.dart';

void main() {
  group('Public Procurement & Resource Allocation Oversight Hive (CAP-105)', () {
    test('ADR-0237 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0237-public-procurement-oversight.md');
      final contract = File('../../docs/contracts/public-procurement-oversight.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-PROCURE-001'));
      expect(contract.readAsStringSync(), contains('OPEN_COMPETITIVE_VERIFIED'));
    });

    test('ProcurementOversightModel instantiates properly', () {
      const model = ProcurementOversightModel(
        tenderId: 'tnd_1',
        contractingAuthority: 'Kadıköy Belediyesi',
        integrityLevel: ProcurementIntegrityLevelModel.openCompetitiveVerified,
        awardedAmountTry: 15400000.0,
        costOverrunPct: 0.02,
        activeCivicAuditorsCount: 128,
      );

      expect(model.awardedAmountTry, 15400000.0);
      expect(model.activeCivicAuditorsCount, 128);
      expect(model.integrityLevel, ProcurementIntegrityLevelModel.openCompetitiveVerified);
    });

    test('InternalAlphaStrings contains Procurement Oversight localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.procureEyebrow, contains('KAMU İHALE VE KAYNAK'));
      expect(tr.procureLvlOpen, contains('Açık Rekabetçi'));

      const en = KefeStrings(Locale('en'));
      expect(en.procureEyebrow, contains('PUBLIC PROCUREMENT'));
      expect(en.procureLvlOpen, contains('Open Competitive'));
    });
  });
}
