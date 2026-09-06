import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/threshold_analysis_models.dart';

void main() {
  group('Threshold Sensitivity Analysis Engine (CAP-018)', () {
    test('ADR-0165 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0165-threshold-sensitivity-analysis-engine.md');
      final contract = File('../../docs/contracts/threshold-sensitivity-analysis.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-THRESHOLD-SENSITIVITY-001'));
      expect(contract.readAsStringSync(), contains('tipping_point_threshold'));
    });

    test('ThresholdAnalysisModel instantiates properly', () {
      const model = ThresholdAnalysisModel(
        caseVersionId: 'case-1',
        parameterName: 'Katkı Payı',
        unit: 'TL',
        tippingPointThreshold: 20.0,
        curvePoints: [
          SensitivityCurvePointModel(parameterValue: 10.0, acceptanceRate: 0.8),
          SensitivityCurvePointModel(parameterValue: 20.0, acceptanceRate: 0.45),
        ],
      );

      expect(model.tippingPointThreshold, 20.0);
      expect(model.curvePoints.length, 2);
    });

    test('InternalAlphaStrings contains Threshold Analysis localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.thresholdEyebrow, contains('EŞİK'));
      expect(tr.thresholdTippingPoint('20', 'TL'), contains('20 TL'));

      const en = KefeStrings(Locale('en'));
      expect(en.thresholdEyebrow, contains('THRESHOLD'));
      expect(en.thresholdTippingPoint('20', 'TL'), contains('20 TL'));
    });
  });
}
