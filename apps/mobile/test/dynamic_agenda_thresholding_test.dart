import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/dynamic_agenda_thresholding_models.dart';

void main() {
  group('Dynamic Agenda Thresholding & Priority Surfacing (CAP-073)', () {
    test('ADR-0222 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0222-dynamic-agenda-thresholding.md');
      final contract = File('../../docs/contracts/dynamic-agenda-thresholding.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-AGENDA-THRESH-001'));
      expect(contract.readAsStringSync(), contains('NATIONAL_URGENCY_SPIKE'));
    });

    test('DynamicAgendaModel instantiates properly', () {
      const model = DynamicAgendaModel(
        topicId: 'top_1',
        topicTitle: 'Yapay Zeka Telif Hakları Yasası',
        priorityTier: AgendaPriorityTierModel.nationalUrgencySpike,
        resonanceVelocityIndex: 0.85,
        viewpointDiversityEntropy: 0.80,
        isFeaturedOnNationalBallot: true,
      );

      expect(model.resonanceVelocityIndex, 0.85);
      expect(model.isFeaturedOnNationalBallot, isTrue);
    });

    test('InternalAlphaStrings contains Dynamic Agenda localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.agendaThrEyebrow, contains('DİNAMİK GÜNDEM'));
      expect(tr.agendaThrTierNational, contains('Ulusal Aciliyet'));

      const en = KefeStrings(Locale('en'));
      expect(en.agendaThrEyebrow, contains('DYNAMIC CIVIC AGENDA'));
      expect(en.agendaThrTierNational, contains('National Urgency'));
    });
  });
}
