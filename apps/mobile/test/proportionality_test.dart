import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/proportionality_models.dart';

void main() {
  group('Proportionality & Least Intrusive Means Engine (CAP-025)', () {
    test('ADR-0184 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0184-proportionality-and-least-intrusive-means-engine.md');
      final contract = File('../../docs/contracts/proportionality-test.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-PROPORTIONALITY-001'));
      expect(contract.readAsStringSync(), contains('PROPORTIONAL_VALID'));
    });

    test('ProportionalityTestModel instantiates properly', () {
      const model = ProportionalityTestModel(
        caseVersionId: 'case-1',
        optionCode: 'OPT_A',
        compositeProportionalityScore: 0.85,
        outcome: ProportionalityOutcomeModel.proportionalValid,
        suitabilityScore: 0.85,
        necessityLeastIntrusiveScore: 0.90,
        strictProportionalityScore: 0.80,
        summary: 'Hedefli denetim ölçülüdür.',
      );

      expect(model.outcome, ProportionalityOutcomeModel.proportionalValid);
      expect(model.compositeProportionalityScore, 0.85);
    });

    test('InternalAlphaStrings contains Proportionality localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.proportionalEyebrow, contains('ÖLÇÜLÜLÜK'));
      expect(tr.proportionalOutcomeValid, contains('Hukuken Geçerli'));

      const en = KefeStrings(Locale('en'));
      expect(en.proportionalEyebrow, contains('PROPORTIONALITY'));
      expect(en.proportionalOutcomeValid, contains('Constitutionally Valid'));
    });
  });
}
