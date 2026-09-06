import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/adaptive_cognitive_load_models.dart';

void main() {
  group('Adaptive Cognitive Load & Information Density (CAP-083)', () {
    test('ADR-0229 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0229-adaptive-cognitive-load.md');
      final contract = File('../../docs/contracts/adaptive-cognitive-load.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-COG-LOAD-001'));
      expect(contract.readAsStringSync(), contains('STREAMLINED_ESSENTIALS'));
    });

    test('AdaptiveCognitiveLoadModel instantiates properly', () {
      const model = AdaptiveCognitiveLoadModel(
        profileId: 'cog_1',
        densityMode: CognitiveDensityModeModel.streamlinedEssentials,
        readingTimeReductionPct: 0.60,
        comprehensionRetentionIndex: 0.92,
        isFatigueMitigationActive: true,
      );

      expect(model.readingTimeReductionPct, 0.60);
      expect(model.comprehensionRetentionIndex, 0.92);
      expect(model.isFatigueMitigationActive, isTrue);
    });

    test('InternalAlphaStrings contains Cognitive Load localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.cogLoadEyebrow, contains('BİLİŞSEL YÜK'));
      expect(tr.cogLoadModeStreamlined, contains('Yalınlaştırılmış'));

      const en = KefeStrings(Locale('en'));
      expect(en.cogLoadEyebrow, contains('ADAPTIVE COGNITIVE'));
      expect(en.cogLoadModeStreamlined, contains('Streamlined'));
    });
  });
}
