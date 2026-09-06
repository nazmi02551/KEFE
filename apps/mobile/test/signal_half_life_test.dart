import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/signal_half_life_models.dart';

void main() {
  group('Signal Half-Life & Freshness Lifecycle Engine (CAP-045)', () {
    test('ADR-0191 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0191-signal-half-life-freshness.md');
      final contract = File('../../docs/contracts/signal-half-life.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-SIGNAL-HALF-LIFE-001'));
      expect(contract.readAsStringSync(), contains('FRESH'));
    });

    test('SignalHalfLifeModel instantiates properly', () {
      const model = SignalHalfLifeModel(
        signalId: 'sig_1',
        caseVersionId: 'case-1',
        halfLifeDays: 90,
        ageDays: 45.0,
        remainingWeight: 0.707,
        freshnessState: FreshnessStateModel.stable,
      );

      expect(model.halfLifeDays, 90);
      expect(model.freshnessState, FreshnessStateModel.stable);
    });

    test('InternalAlphaStrings contains Signal Half-Life localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.halflifeEyebrow, contains('SİNYAL YARI ÖMRÜ'));
      expect(tr.halflifeStateFresh, contains('Taze'));

      const en = KefeStrings(Locale('en'));
      expect(en.halflifeEyebrow, contains('SIGNAL HALF-LIFE'));
      expect(en.halflifeStateFresh, contains('Fresh'));
    });
  });
}
