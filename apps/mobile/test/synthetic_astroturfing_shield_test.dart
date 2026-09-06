import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/synthetic_astroturfing_shield_models.dart';

void main() {
  group('Synthetic Argument & Astroturfing Bot Shield (CAP-092)', () {
    test('ADR-0232 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0232-synthetic-astroturfing-shield.md');
      final contract = File('../../docs/contracts/synthetic-astroturfing-shield.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-BOT-SHIELD-001'));
      expect(contract.readAsStringSync(), contains('ISOLATED_QUARANTINE_SWARM'));
    });

    test('BotShieldModel instantiates properly', () {
      const model = BotShieldModel(
        clusterId: 'bot_1',
        targetCaseId: 'case_1',
        defenseState: BotDefenseStateModel.isolatedQuarantineSwarm,
        syntheticProbabilityScore: 0.94,
        quarantinedBotPayloadsCount: 1450,
        semanticEntropyIndex: 0.12,
      );

      expect(model.syntheticProbabilityScore, 0.94);
      expect(model.quarantinedBotPayloadsCount, 1450);
      expect(model.defenseState, BotDefenseStateModel.isolatedQuarantineSwarm);
    });

    test('InternalAlphaStrings contains Bot Shield localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.botShieldEyebrow, contains('SENTETİK ASTROTURFING'));
      expect(tr.botShieldStQuarantine, contains('Karantinaya Alındı'));

      const en = KefeStrings(Locale('en'));
      expect(en.botShieldEyebrow, contains('SYNTHETIC ASTROTURFING'));
      expect(en.botShieldStQuarantine, contains('Quarantined'));
    });
  });
}
