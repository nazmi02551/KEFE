import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/impact_verification_models.dart';

void main() {
  group('Impact Verification & Milestone Outcome (CAP-054)', () {
    test('ADR-0195 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0195-impact-verification.md');
      final contract = File('../../docs/contracts/impact-verification.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-IMPACT-VERIFY-001'));
      expect(contract.readAsStringSync(), contains('FULL_RESOLUTION'));
    });

    test('ImpactVerificationModel instantiates properly', () {
      const model = ImpactVerificationModel(
        verificationId: 'ver_1',
        actionId: 'act_1',
        outcomeVerdict: OutcomeVerdictModel.fullResolution,
        resolutionScore: 0.92,
        auditorConsensusCount: 12,
        verificationNotes: 'Tesis faaliyete geçti ve su kalitesi doğrulandı.',
      );

      expect(model.resolutionScore, 0.92);
      expect(model.outcomeVerdict, OutcomeVerdictModel.fullResolution);
    });

    test('InternalAlphaStrings contains Impact Verification localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.impactVerEyebrow, contains('TOPLULUK ETKİ'));
      expect(tr.impactVerVerdictFull, contains('Tam Çözüm'));

      const en = KefeStrings(Locale('en'));
      expect(en.impactVerEyebrow, contains('COMMUNITY IMPACT'));
      expect(en.impactVerVerdictFull, contains('Full Resolution'));
    });
  });
}
