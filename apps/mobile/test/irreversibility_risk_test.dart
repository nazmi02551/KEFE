import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/irreversibility_risk_models.dart';

void main() {
  group('Irreversibility Risk Analyzer (CAP-021)', () {
    test('ADR-0179 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0179-irreversibility-and-reversibility-risk-analyzer.md');
      final contract = File('../../docs/contracts/irreversibility-risk-analyzer.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-IRREVERSIBILITY-001'));
      expect(contract.readAsStringSync(), contains('PERMANENTLY_IRREVERSIBLE'));
    });

    test('IrreversibilityRiskModel instantiates properly', () {
      const model = IrreversibilityRiskModel(
        caseVersionId: 'case-1',
        optionCode: 'OPT_A',
        reversibilityClass: ReversibilityClassModel.permanentlyIrreversible,
        precautionaryRiskScore: 1.0,
        unwindTimeMonths: 120,
        unwindCostFactor: 0.95,
        riskSummary: 'Kalıcı ekolojik hasar.',
      );

      expect(model.reversibilityClass, ReversibilityClassModel.permanentlyIrreversible);
      expect(model.precautionaryRiskScore, 1.0);
    });

    test('InternalAlphaStrings contains Irreversibility localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.irreversibleEyebrow, contains('GERİ DÖNÜŞ'));
      expect(tr.irreversibleClassPerm, contains('Kalıcı ve Geri'));

      const en = KefeStrings(Locale('en'));
      expect(en.irreversibleEyebrow, contains('REVERSIBILITY'));
      expect(en.irreversibleClassPerm, contains('Permanently'));
    });
  });
}
