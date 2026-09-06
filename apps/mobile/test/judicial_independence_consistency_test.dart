import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/judicial_independence_consistency_models.dart';

void main() {
  group('Judicial Independence & Jurisprudential Consistency Chamber (CAP-109)', () {
    test('ADR-0241 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0241-judicial-independence-consistency.md');
      final contract = File('../../docs/contracts/judicial-independence-consistency.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-JUDICIAL-001'));
      expect(contract.readAsStringSync(), contains('PRECEDENT_ALIGNED_CONSISTENT'));
    });

    test('JudicialConsistencyModel instantiates properly', () {
      const model = JudicialConsistencyModel(
        chamberId: 'jdc_1',
        courtJurisdiction: 'Danıştay 6. Dairesi',
        caseCategory: 'Kentsel Dönüşüm',
        consistencyStatus: JurisprudentialConsistencyStatusModel.precedentAlignedConsistent,
        precedentFidelityScore: 0.92,
        evaluatedPrecedentCasesCount: 48,
      );

      expect(model.precedentFidelityScore, 0.92);
      expect(model.evaluatedPrecedentCasesCount, 48);
      expect(model.consistencyStatus, JurisprudentialConsistencyStatusModel.precedentAlignedConsistent);
    });

    test('InternalAlphaStrings contains Judicial Independence localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.judicialEyebrow, contains('YARGI BAĞIMSIZLIĞI'));
      expect(tr.judicialStAligned, contains('İçtihatla Uyumlu'));

      const en = KefeStrings(Locale('en'));
      expect(en.judicialEyebrow, contains('JUDICIAL INDEPENDENCE'));
      expect(en.judicialStAligned, contains('Precedent-Aligned'));
    });
  });
}
