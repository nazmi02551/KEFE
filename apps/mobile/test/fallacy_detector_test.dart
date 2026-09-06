import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/fallacy_detector_models.dart';

void main() {
  group('Cognitive Fallacy and Distortion Detector (CAP-042)', () {
    test('ADR-0177 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0177-cognitive-fallacy-and-distortion-detector.md');
      final contract = File('../../docs/contracts/fallacy-distortion-detector.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-FALLACY-DETECTOR-001'));
      expect(contract.readAsStringSync(), contains('STRAW_MAN'));
    });

    test('FallacyDetectionResultModel instantiates properly', () {
      const model = FallacyDetectionResultModel(
        argumentId: 'arg-1',
        hasFallacy: true,
        overallIntegrityScore: 0.70,
        detectedFallacies: [
          DetectedFallacyItemModel(
            fallacyType: FallacyTypeModel.strawMan,
            confidence: 0.8,
            explanation: 'Karşıt görüş çarpıtılmış.',
          ),
        ],
      );

      expect(model.hasFallacy, isTrue);
      expect(model.overallIntegrityScore, 0.70);
      expect(model.detectedFallacies.first.fallacyType, FallacyTypeModel.strawMan);
    });

    test('InternalAlphaStrings contains Fallacy localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.fallacyEyebrow, contains('SAFSATA'));
      expect(tr.fallacyTypeStrawMan, contains('Korkuluk'));

      const en = KefeStrings(Locale('en'));
      expect(en.fallacyEyebrow, contains('FALLACY'));
      expect(en.fallacyTypeStrawMan, contains('Straw Man'));
    });
  });
}
