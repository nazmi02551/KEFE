import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/revolving_door_monitor_models.dart';

void main() {
  group('Revolving Door & Political Transition Monitor (CAP-106)', () {
    test('ADR-0238 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0238-revolving-door-monitor.md');
      final contract = File('../../docs/contracts/revolving-door-monitor.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-REVOLVE-001'));
      expect(contract.readAsStringSync(), contains('COOLING_OFF_COMPLIANT'));
    });

    test('RevolvingDoorModel instantiates properly', () {
      const model = RevolvingDoorModel(
        transitionId: 'rvl_1',
        officialNameAnonymized: 'Eski BDDK Kurul Üyesi #A8',
        status: TransitionStatusModel.coolingOffCompliant,
        coolingOffMonthsObserved: 36,
        captureRiskScore: 0.10,
        regulatoryAgencySource: 'Bankacılık Düzenleme ve Denetleme Kurumu',
      );

      expect(model.coolingOffMonthsObserved, 36);
      expect(model.captureRiskScore, 0.10);
      expect(model.status, TransitionStatusModel.coolingOffCompliant);
    });

    test('InternalAlphaStrings contains Revolving Door localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.revolveEyebrow, contains('DÖNER KAPI'));
      expect(tr.revolveStCompliant, contains('Soğuma Süresine'));

      const en = KefeStrings(Locale('en'));
      expect(en.revolveEyebrow, contains('REVOLVING DOOR'));
      expect(en.revolveStCompliant, contains('Cooling-Off'));
    });
  });
}
