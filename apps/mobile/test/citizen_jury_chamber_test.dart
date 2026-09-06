import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/citizen_jury_chamber_models.dart';

void main() {
  group('Citizen Jury & Sortition Deliberation Chamber (CAP-046)', () {
    test('ADR-0223 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0223-citizen-jury-chamber.md');
      final contract = File('../../docs/contracts/citizen-jury-chamber.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-JURY-CHAMBER-001'));
      expect(contract.readAsStringSync(), contains('CONSENSUS_VERDICT_EMITTED'));
    });

    test('CitizenJuryModel instantiates properly', () {
      const model = CitizenJuryModel(
        juryId: 'jury_1',
        dilemmaTitle: 'Yapay Zeka ve Otonom Araçlar Düzenlemesi',
        stage: CitizenJuryStageModel.consensusVerdictEmitted,
        jurorCount: 24,
        expertWitnessesCount: 4,
        verdictConsensusRate: 0.88,
      );

      expect(model.jurorCount, 24);
      expect(model.verdictConsensusRate, 0.88);
    });

    test('InternalAlphaStrings contains Citizen Jury localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.citJuryEyebrow, contains('YURTTAŞ KARAR HEYETİ'));
      expect(tr.citJuryStAssembly, contains('Tabakalı Rastlantısal'));

      const en = KefeStrings(Locale('en'));
      expect(en.citJuryEyebrow, contains('CITIZEN JURY'));
      expect(en.citJuryStAssembly, contains('Stratified Random'));
    });
  });
}
