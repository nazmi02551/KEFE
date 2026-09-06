import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/cross_case_similarity_models.dart';

void main() {
  group('Cross-Case Similarity & Comparative Matrix (CAP-101)', () {
    test('ADR-0214 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0214-cross-case-similarity.md');
      final contract = File('../../docs/contracts/cross-case-similarity.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-CROSS-SIM-001'));
      expect(contract.readAsStringSync(), contains('HIGH_TOPOLOGICAL_ANALOGUE'));
    });

    test('CrossCaseSimilarityModel instantiates properly', () {
      const model = CrossCaseSimilarityModel(
        sourceCaseId: 'src_1',
        targetCaseId: 'tgt_1',
        targetCaseTitle: 'Tarihsel Su Krizi (1994)',
        similarityScore: 0.88,
        alignmentTier: SimilarityAlignmentTierModel.highTopologicalAnalogue,
        sharedTensionSummary: 'Sınırlı kamu kaynağının adil bölüşümü.',
      );

      expect(model.similarityScore, 0.88);
      expect(model.alignmentTier, SimilarityAlignmentTierModel.highTopologicalAnalogue);
    });

    test('InternalAlphaStrings contains Cross-Case Similarity localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.crossSimEyebrow, contains('ÇAPRAZ VAKA KARŞILAŞTIRMA'));
      expect(tr.crossSimTierHigh, contains('Yüksek Topolojik'));

      const en = KefeStrings(Locale('en'));
      expect(en.crossSimEyebrow, contains('CROSS-CASE SIMILARITY'));
      expect(en.crossSimTierHigh, contains('High Topological'));
    });
  });
}
