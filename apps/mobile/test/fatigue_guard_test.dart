import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/fatigue_guard_models.dart';

void main() {
  group('Decision Fatigue & Healthy Pacing Guard (CAP-014)', () {
    test('ADR-0190 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0190-decision-fatigue-guard.md');
      final contract = File('../../docs/contracts/decision-fatigue-guard.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-FATIGUE-GUARD-001'));
      expect(contract.readAsStringSync(), contains('OPTIMAL_PACING'));
    });

    test('DecisionFatigueModel instantiates properly', () {
      const model = DecisionFatigueModel(
        sessionId: 'sess_1',
        consecutiveWeighCount: 6,
        sessionDurationMinutes: 25.0,
        pacingStatus: PacingStatusModel.pacingRecommended,
        gentleRecommendationPrompt: 'Kısa bir mola vermeniz önerilir.',
      );

      expect(model.consecutiveWeighCount, 6);
      expect(model.pacingStatus, PacingStatusModel.pacingRecommended);
    });

    test('InternalAlphaStrings contains Decision Fatigue localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.fatigueEyebrow, contains('SAĞLIKLI RİTİM'));
      expect(tr.fatigueStatusOptimal, contains('Odaklanmış ve Dengeli'));

      const en = KefeStrings(Locale('en'));
      expect(en.fatigueEyebrow, contains('HEALTHY PACING'));
      expect(en.fatigueStatusOptimal, contains('Focused & Optimal'));
    });
  });
}
