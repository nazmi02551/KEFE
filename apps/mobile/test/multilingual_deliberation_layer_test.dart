import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/multilingual_deliberation_layer_models.dart';

void main() {
  group('Multilingual Universal Deliberation & Translation Layer (CAP-080)', () {
    test('ADR-0226 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0226-multilingual-deliberation-layer.md');
      final contract = File('../../docs/contracts/multilingual-deliberation-layer.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-MULTI-LOC-001'));
      expect(contract.readAsStringSync(), contains('HIGH_FIDELITY_CERTIFIED'));
    });

    test('MultilingualTranslationModel instantiates properly', () {
      const model = MultilingualTranslationModel(
        translationId: 'tra_1',
        sourceLocale: 'tr',
        targetLocale: 'en',
        fidelityTier: TranslationFidelityTierModel.highFidelityCertified,
        semanticSimilarityScore: 0.96,
        translatedText: 'Algorithmic transparency is essential.',
      );

      expect(model.sourceLocale, 'tr');
      expect(model.targetLocale, 'en');
      expect(model.semanticSimilarityScore, 0.96);
    });

    test('InternalAlphaStrings contains Multilingual localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.multiLocEyebrow, contains('ÇOK DİLLİ'));
      expect(tr.multiLocTierCertified, contains('Yüksek Doğruluklu'));

      const en = KefeStrings(Locale('en'));
      expect(en.multiLocEyebrow, contains('MULTILINGUAL'));
      expect(en.multiLocTierCertified, contains('High-Fidelity'));
    });
  });
}
