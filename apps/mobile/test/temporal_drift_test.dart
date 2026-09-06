import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/temporal_drift_models.dart';

void main() {
  group('Temporal Retest and Drift Engine (CAP-013)', () {
    test('ADR-0173 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0173-temporal-retest-and-drift-engine.md');
      final contract = File('../../docs/contracts/temporal-retest-drift.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-TEMPORAL-DRIFT-001'));
      expect(contract.readAsStringSync(), contains('MATURED_REVISION'));
    });

    test('TemporalDriftModel instantiates properly', () {
      const model = TemporalDriftModel(
        caseVersionId: 'case-1',
        initialOptionCode: 'OPT_A',
        retestOptionCode: 'OPT_B',
        timeElapsedDays: 45,
        isShifted: true,
        confidenceDelta: 0.2,
        driftNature: DriftNatureModel.maturedRevision,
      );

      expect(model.isShifted, isTrue);
      expect(model.timeElapsedDays, 45);
      expect(model.driftNature, DriftNatureModel.maturedRevision);
    });

    test('InternalAlphaStrings contains Temporal Drift localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.driftEyebrow, contains('ZAMANSAL FİKİR'));
      expect(tr.driftNatureMatured, contains('Olgunlaşmış'));

      const en = KefeStrings(Locale('en'));
      expect(en.driftEyebrow, contains('TEMPORAL DRIFT'));
      expect(en.driftNatureMatured, contains('Matured'));
    });
  });
}
