import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/future_generations_models.dart';

void main() {
  group('Future Generations Projection Engine (CAP-020)', () {
    test('ADR-0178 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0178-long-term-future-generations-projection-engine.md');
      final contract = File('../../docs/contracts/future-generations-projection.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-FUTURE-GEN-001'));
      expect(contract.readAsStringSync(), contains('HORIZON_100_YEARS'));
    });

    test('FutureGenerationsModel instantiates properly', () {
      const model = FutureGenerationsModel(
        caseVersionId: 'case-1',
        optionCode: 'OPT_A',
        netIntergenerationalScore: 0.75,
        projections: [
          HorizonProjectionItemModel(
            horizon: TimeHorizonModel.horizon20Years,
            impactScore: 0.80,
            summary: '20 yıllık temiz enerji bağımsızlığı.',
          ),
        ],
      );

      expect(model.netIntergenerationalScore, 0.75);
      expect(model.projections.length, 1);
    });

    test('InternalAlphaStrings contains Future Generations localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.futureGenEyebrow, contains('GELECEK KUŞAKLAR'));
      expect(tr.futureGenH100Yr, contains('100 Yıllık'));

      const en = KefeStrings(Locale('en'));
      expect(en.futureGenEyebrow, contains('FUTURE GENERATIONS'));
      expect(en.futureGenH100Yr, contains('100-Year'));
    });
  });
}
