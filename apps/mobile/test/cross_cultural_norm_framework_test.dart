import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/cross_cultural_norm_framework_models.dart';

void main() {
  group('Cross-Cultural Norm Framework & Localized Values (CAP-081)', () {
    test('ADR-0227 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0227-cross-cultural-norm-framework.md');
      final contract = File('../../docs/contracts/cross-cultural-norm-framework.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-CULT-NORM-001'));
      expect(contract.readAsStringSync(), contains('COMMUNITY_SOLIDARITY_AND_MUTUALITY'));
    });

    test('CulturalNormModel instantiates properly', () {
      const model = CulturalNormModel(
        frameworkId: 'cn_1',
        regionIdentifier: 'TR-MARMARA',
        primaryDimension: CulturalNormDimensionModel.communitySolidarityAndMutuality,
        culturalAlignmentScore: 0.92,
        universalBaselineCompliance: true,
        normSynthesisSummary: 'İmece ve dayanışma geleneği ile modern şeffaflık sentezi.',
      );

      expect(model.regionIdentifier, 'TR-MARMARA');
      expect(model.culturalAlignmentScore, 0.92);
      expect(model.universalBaselineCompliance, isTrue);
    });

    test('InternalAlphaStrings contains Cross Cultural localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.cultNormEyebrow, contains('ÇAPRAZ KÜLTÜREL'));
      expect(tr.cultNormDimSolidarity, contains('Toplumsal Dayanışma'));

      const en = KefeStrings(Locale('en'));
      expect(en.cultNormEyebrow, contains('CROSS-CULTURAL'));
      expect(en.cultNormDimSolidarity, contains('Community Solidarity'));
    });
  });
}
