import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/blind_variants_models.dart';

void main() {
  group('Blind-First Variants Engine (CAP-005)', () {
    test('ADR-0186 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0186-blind-first-variants-engine.md');
      final contract = File('../../docs/contracts/blind-first-variants.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-BLIND-VARIANTS-001'));
      expect(contract.readAsStringSync(), contains('ACTOR_BLIND'));
    });

    test('BlindVariantsModel instantiates properly', () {
      const model = BlindVariantsModel(
        caseVersionId: 'case-1',
        blindMode: BlindModeModel.actorBlind,
        blindedPrompt: 'Bir kamu görevlisi belgeleri sızdırdı.',
        realIdentityRevealed: 'Edward Snowden (2013)',
        neutralityScore: 0.90,
      );

      expect(model.blindMode, BlindModeModel.actorBlind);
      expect(model.neutralityScore, 0.90);
    });

    test('InternalAlphaStrings contains Blind Variants localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.blindEyebrow, contains('KÖR/TARAFSIZ'));
      expect(tr.blindModeActor, contains('Aktör Körlemesi'));

      const en = KefeStrings(Locale('en'));
      expect(en.blindEyebrow, contains('BLIND-FIRST'));
      expect(en.blindModeActor, contains('Actor Blind'));
    });
  });
}
