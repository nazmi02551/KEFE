import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/temporal_opinion_flow_models.dart';

void main() {
  group('Temporal Flow & Animated Opinion Migration (CAP-100)', () {
    test('ADR-0213 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0213-temporal-opinion-flow.md');
      final contract = File('../../docs/contracts/temporal-opinion-flow.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-OPINION-FLOW-001'));
      expect(contract.readAsStringSync(), contains('MID_DELIBERATION_SHIFT'));
    });

    test('TemporalOpinionFlowModel instantiates properly', () {
      const model = TemporalOpinionFlowModel(
        flowId: 'flow_1',
        caseVersionId: 'case_1',
        epochType: MigrationEpochTypeModel.midDeliberationShift,
        optionAShare: 0.45,
        optionBShare: 0.35,
        undecidedBridgeShare: 0.20,
        migrationRate: 0.18,
      );

      expect(model.migrationRate, 0.18);
      expect(model.epochType, MigrationEpochTypeModel.midDeliberationShift);
    });

    test('InternalAlphaStrings contains Temporal Flow localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.tempFlowEyebrow, contains('ZAMAN BOYUTLU FİKİR'));
      expect(tr.tempFlowEpochInitial, contains('Kör Tartım'));

      const en = KefeStrings(Locale('en'));
      expect(en.tempFlowEyebrow, contains('TEMPORAL OPINION'));
      expect(en.tempFlowEpochInitial, contains('Blind First'));
    });
  });
}
