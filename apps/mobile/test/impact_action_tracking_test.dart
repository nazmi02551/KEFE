import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/impact_action_tracking_models.dart';

void main() {
  group('Institution Action & Promise Tracker (CAP-052)', () {
    test('ADR-0193 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0193-impact-action-tracking.md');
      final contract = File('../../docs/contracts/impact-action-tracking.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-ACTION-TRACKING-001'));
      expect(contract.readAsStringSync(), contains('PROMISED'));
    });

    test('ImpactActionModel instantiates properly', () {
      const model = ImpactActionModel(
        actionId: 'act_1',
        institutionName: 'İBB Çevre Dairesi',
        pledgeTitle: 'Filtreleme İstasyonu İnşası',
        milestoneStatus: MilestoneStatusModel.inProgress,
        completionPercentage: 65,
        targetCompletionUtc: '2026-12-31T00:00:00Z',
      );

      expect(model.completionPercentage, 65);
      expect(model.milestoneStatus, MilestoneStatusModel.inProgress);
    });

    test('InternalAlphaStrings contains Impact Action Tracking localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.actionTrackEyebrow, contains('KURUM EYLEM'));
      expect(tr.actionTrackStatusProgress, contains('Uygulamada'));

      const en = KefeStrings(Locale('en'));
      expect(en.actionTrackEyebrow, contains('INSTITUTION ACTION'));
      expect(en.actionTrackStatusProgress, contains('In Progress'));
    });
  });
}
