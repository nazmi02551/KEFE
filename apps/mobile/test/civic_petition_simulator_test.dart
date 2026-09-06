import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/civic_petition_simulator_models.dart';

void main() {
  group('Civic Petition & Legislative Impact Simulator (CAP-079)', () {
    test('ADR-0225 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0225-civic-petition-simulator.md');
      final contract = File('../../docs/contracts/civic-petition-simulator.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-PETITION-SIM-001'));
      expect(contract.readAsStringSync(), contains('SUBMITTED_TO_PARLIAMENT'));
    });

    test('CivicPetitionModel instantiates properly', () {
      const model = CivicPetitionModel(
        petitionId: 'pet_1',
        billTitle: 'Dönüştürülebilir Ambalaj Zorunluluğu Kanunu',
        stage: PetitionStageModel.submittedToParliament,
        signaturesCount: 120000,
        signatureTargetThreshold: 100000,
        projectedNetBenefitScore: 0.78,
      );

      expect(model.signaturesCount, 120000);
      expect(model.projectedNetBenefitScore, 0.78);
      expect(model.stage, PetitionStageModel.submittedToParliament);
    });

    test('InternalAlphaStrings contains Civic Petition localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.civPetEyebrow, contains('SİVİL DİLEKÇE'));
      expect(tr.civPetStSubmitted, contains('Meclis Komisyon'));

      const en = KefeStrings(Locale('en'));
      expect(en.civPetEyebrow, contains('CIVIC PETITION'));
      expect(en.civPetStSubmitted, contains('Parliamentary Hearing'));
    });
  });
}
