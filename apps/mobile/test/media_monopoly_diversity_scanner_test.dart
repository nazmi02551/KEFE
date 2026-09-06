import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/media_monopoly_diversity_scanner_models.dart';

void main() {
  group('Media Monopoly & Source Diversity Scanner (CAP-111)', () {
    test('ADR-0243 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0243-media-monopoly-diversity-scanner.md');
      final contract = File('../../docs/contracts/media-monopoly-diversity-scanner.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-MEDIA-001'));
      expect(contract.readAsStringSync(), contains('PLURALISTIC_INDEPENDENT_DIVERSE'));
    });

    test('MediaDiversityModel instantiates properly', () {
      const model = MediaDiversityModel(
        scannerId: 'med_1',
        topicCluster: 'İklim Değişikliği',
        pluralismLevel: MediaPluralismLevelModel.pluralisticIndependentDiverse,
        sourceDiversityIndex: 0.88,
        independentOutletsCount: 12,
      );

      expect(model.sourceDiversityIndex, 0.88);
      expect(model.independentOutletsCount, 12);
      expect(model.pluralismLevel, MediaPluralismLevelModel.pluralisticIndependentDiverse);
    });

    test('InternalAlphaStrings contains Media Monopoly localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.mediaScanEyebrow, contains('MEDYA TEKELLEŞMESİ'));
      expect(tr.mediaScanLvlPluralistic, contains('Çoğulcu ve Bağımsız'));

      const en = KefeStrings(Locale('en'));
      expect(en.mediaScanEyebrow, contains('MEDIA MONOPOLY'));
      expect(en.mediaScanLvlPluralistic, contains('Pluralistic & Independent'));
    });
  });
}
