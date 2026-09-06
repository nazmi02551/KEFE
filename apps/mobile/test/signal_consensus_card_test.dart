import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/signal/domain/signal_consensus_card_models.dart';

void main() {
  group('Signal and Consensus Card Composition (CAP-016)', () {
    test('ADR-0164 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0164-signal-and-consensus-card-composition.md');
      final contract = File('../../docs/contracts/signal-consensus-card.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-SIGNAL-CONSENSUS-CARD-001'));
      expect(contract.readAsStringSync(), contains('confidence_tier'));
    });

    test('SignalConsensusCardModel instantiates properly', () {
      final card = SignalConsensusCardModel(
        signalId: 'sig-1',
        caseVersionId: 'case-1',
        caseTitle: 'Çocuk Güvenliği Düzenlemesi',
        consensusStatement: '16 yaş altı kullanıcılar için gece sınırlaması uygulanmalıdır.',
        agreementPercentage: 82.5,
        sampleSize: 1500,
        confidenceTier: SignalConfidenceTierModel.gold,
        certifiedAt: DateTime.now().toUtc(),
      );

      expect(card.signalId, 'sig-1');
      expect(card.confidenceTier, SignalConfidenceTierModel.gold);
      expect(card.agreementPercentage, 82.5);
    });

    test('InternalAlphaStrings contains Signal Card localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.signalCardEyebrow, contains('SİNYALİ'));
      expect(tr.signalCardTierGold, contains('Altın'));

      const en = KefeStrings(Locale('en'));
      expect(en.signalCardEyebrow, contains('SIGNAL'));
      expect(en.signalCardTierGold, contains('Gold'));
    });
  });
}
