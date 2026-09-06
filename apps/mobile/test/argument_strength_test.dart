import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/argument_strength_models.dart';

void main() {
  group('Argument Strength and Validity Evaluator (CAP-041)', () {
    test('ADR-0176 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0176-argument-strength-and-validity-evaluator.md');
      final contract = File('../../docs/contracts/argument-strength-validity.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-ARGUMENT-STRENGTH-001'));
      expect(contract.readAsStringSync(), contains('TIER_A_ROBUST'));
    });

    test('ArgumentStrengthModel instantiates properly', () {
      const model = ArgumentStrengthModel(
        argumentId: 'arg-1',
        empiricalFoundationScore: 0.85,
        logicalConsistencyScore: 0.90,
        representativeBalanceScore: 0.75,
        compositeStrengthScore: 0.85,
        strengthTier: ArgumentStrengthTierModel.tierARobust,
      );

      expect(model.strengthTier, ArgumentStrengthTierModel.tierARobust);
      expect(model.compositeStrengthScore, 0.85);
    });

    test('InternalAlphaStrings contains Argument Strength localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.argStrengthEyebrow, contains('ARGÜMAN GÜCÜ'));
      expect(tr.argStrengthTierRobust, contains('Kademe A'));

      const en = KefeStrings(Locale('en'));
      expect(en.argStrengthEyebrow, contains('ARGUMENT STRENGTH'));
      expect(en.argStrengthTierRobust, contains('Tier A'));
    });
  });
}
