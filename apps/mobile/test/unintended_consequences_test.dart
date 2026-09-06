import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/unintended_consequences_models.dart';

void main() {
  group('Unintended Consequences Simulator (CAP-022)', () {
    test('ADR-0180 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0180-secondary-and-unintended-consequences-simulator.md');
      final contract = File('../../docs/contracts/unintended-consequences.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-UNINTENDED-CONSEQUENCES-001'));
      expect(contract.readAsStringSync(), contains('PERVERSE_INCENTIVE'));
    });

    test('UnintendedConsequencesModel instantiates properly', () {
      const model = UnintendedConsequencesModel(
        caseVersionId: 'case-1',
        optionCode: 'OPT_A',
        overallSystemicRisk: ConsequenceSeverityModel.severeParadox,
        consequences: [
          UnintendedConsequenceItemModel(
            consequenceType: ConsequenceTypeModel.perverseIncentive,
            severity: ConsequenceSeverityModel.severeParadox,
            mitigationFeasibility: 0.40,
            description: 'Kobra etkisi: Evlerin piyasadan çekilmesi.',
          ),
        ],
      );

      expect(model.overallSystemicRisk, ConsequenceSeverityModel.severeParadox);
      expect(model.consequences.first.consequenceType, ConsequenceTypeModel.perverseIncentive);
    });

    test('InternalAlphaStrings contains Unintended Consequences localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.unintendedEyebrow, contains('BEKLENMEYEN SONUÇLAR'));
      expect(tr.unintendedTypePerverse, contains('Tersine Teşvik'));

      const en = KefeStrings(Locale('en'));
      expect(en.unintendedEyebrow, contains('UNINTENDED CONSEQUENCES'));
      expect(en.unintendedTypePerverse, contains('Perverse Incentive'));
    });
  });
}
