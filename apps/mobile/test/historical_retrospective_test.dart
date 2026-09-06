import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/historical_retrospective_models.dart';

void main() {
  group('Historical Decision Retrospective Engine (CAP-028)', () {
    test('ADR-0198 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0198-historical-retrospective.md');
      final contract = File('../../docs/contracts/historical-retrospective.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-RETRO-SIM-001'));
      expect(contract.readAsStringSync(), contains('TWENTIETH_CENTURY'));
    });

    test('HistoricalRetrospectiveModel instantiates properly', () {
      const model = HistoricalRetrospectiveModel(
        retrospectiveId: 'retro_1',
        caseVersionId: 'case-1',
        historicalEra: HistoricalEraModel.twentiethCentury,
        historicalYear: 1973,
        historicalEventName: '1973 Petrol Krizi',
        actualHistoricalDecision: 'Hız sınırı 55 mph yapıldı.',
        historicalConsequenceSummary: 'Yakıt tüketimi azaldı.',
      );

      expect(model.historicalYear, 1973);
      expect(model.historicalEra, HistoricalEraModel.twentiethCentury);
    });

    test('InternalAlphaStrings contains Historical Retrospective localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.retroSimEyebrow, contains('TARİHSEL KARAR'));
      expect(tr.retroSimEraCentury20, contains('20. Yüzyıl'));

      const en = KefeStrings(Locale('en'));
      expect(en.retroSimEyebrow, contains('HISTORICAL RETROSPECTIVE'));
      expect(en.retroSimEraCentury20, contains('20th-Century'));
    });
  });
}
