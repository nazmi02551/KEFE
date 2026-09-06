import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/multi_stakeholder_consensus_circle_models.dart';

void main() {
  group('Multi-Stakeholder Consensus Circle & Synthesis (CAP-047)', () {
    test('ADR-0224 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0224-multi-stakeholder-consensus-circle.md');
      final contract = File('../../docs/contracts/multi-stakeholder-consensus-circle.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-CONS-CIRCLE-001'));
      expect(contract.readAsStringSync(), contains('SYNTHESIS_PACT_RATIFIED'));
    });

    test('ConsensusCircleModel instantiates properly', () {
      const model = ConsensusCircleModel(
        circleId: 'crc_1',
        pactTitle: 'Sanayi Emisyonları Uzlaşı Sözleşmesi',
        state: ConsensusCircleStateModel.synthesisPactRatified,
        stakeholderGroupsCount: 4,
        mutualConcessionScore: 0.85,
        synthesisCovenantSummary: 'Aşamalı filtreleme ve bağımsız izleme mutabakatı.',
      );

      expect(model.stakeholderGroupsCount, 4);
      expect(model.mutualConcessionScore, 0.85);
      expect(model.state, ConsensusCircleStateModel.synthesisPactRatified);
    });

    test('InternalAlphaStrings contains Consensus Circle localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.consCrcEyebrow, contains('ÇOKLU PAYDAŞLI'));
      expect(tr.consCrcStRatified, contains('Sözleşmesi Onaylandı'));

      const en = KefeStrings(Locale('en'));
      expect(en.consCrcEyebrow, contains('MULTI-STAKEHOLDER'));
      expect(en.consCrcStRatified, contains('Pact Ratified'));
    });
  });
}
