import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/divergence_anatomy_models.dart';

void main() {
  group('Divergence Anatomy Breakdown Engine (CAP-040)', () {
    test('ADR-0163 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0163-divergence-anatomy-breakdown-engine.md');
      final contract = File('../../docs/contracts/divergence-anatomy.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-DIVERGENCE-ANATOMY-001'));
      expect(contract.readAsStringSync(), contains('NORMATIVE_VALUE_WEIGHT'));
    });

    test('DivergenceAnatomyModel instantiates properly', () {
      const model = DivergenceAnatomyModel(
        caseVersionId: 'case-v1',
        primaryDriver: DivergenceDriverTypeModel.normativeValueWeight,
        drivers: [
          DivergenceDriverItemModel(
            driverType: DivergenceDriverTypeModel.normativeValueWeight,
            sharePercentage: 60.0,
            explanation: 'Değer önceliklendirmesi.',
          ),
          DivergenceDriverItemModel(
            driverType: DivergenceDriverTypeModel.factualProbabilityAssessment,
            sharePercentage: 40.0,
            explanation: 'Risk algısı.',
          ),
        ],
      );

      expect(model.primaryDriver, DivergenceDriverTypeModel.normativeValueWeight);
      expect(model.drivers.length, 2);
    });

    test('InternalAlphaStrings contains Divergence Anatomy localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.anatomyEyebrow, contains('ANATOMİSİ'));
      expect(tr.anatomyDriverNormative, contains('Ahlaki'));

      const en = KefeStrings(Locale('en'));
      expect(en.anatomyEyebrow, contains('ANATOMY'));
      expect(en.anatomyDriverNormative, contains('Moral'));
    });
  });
}
