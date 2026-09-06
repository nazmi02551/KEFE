import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/civic_literacy_workshop_models.dart';

void main() {
  group('Education Mode & Civic Literacy Workshop (CAP-031)', () {
    test('ADR-0206 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0206-civic-literacy-workshop.md');
      final contract = File('../../docs/contracts/civic-literacy-workshop.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-CIVIC-WORKSHOP-001'));
      expect(contract.readAsStringSync(), contains('FALLACY_SPOTTING'));
    });

    test('CivicLiteracyWorkshopModel instantiates properly', () {
      const model = CivicLiteracyWorkshopModel(
        workshopId: 'wsp_1',
        moduleType: LiteracyModuleTypeModel.fallacySpotting,
        moduleTitle: 'Safsata Teşhisi',
        totalDrills: 10,
        completedDrills: 8,
        comprehensionScore: 0.88,
      );

      expect(model.comprehensionScore, 0.88);
      expect(model.moduleType, LiteracyModuleTypeModel.fallacySpotting);
    });

    test('InternalAlphaStrings contains Civic Literacy localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.civicWorkEyebrow, contains('EĞİTİM MODU'));
      expect(tr.civicWorkModFallacy, contains('Safsata'));

      const en = KefeStrings(Locale('en'));
      expect(en.civicWorkEyebrow, contains('EDUCATION MODE'));
      expect(en.civicWorkModFallacy, contains('Fallacy'));
    });
  });
}
