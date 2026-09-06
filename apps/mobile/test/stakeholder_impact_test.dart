import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/stakeholder_impact_models.dart';

void main() {
  group('Stakeholder Impact Matrix Engine (CAP-023)', () {
    test('ADR-0166 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0166-stakeholder-impact-matrix-engine.md');
      final contract = File('../../docs/contracts/stakeholder-impact-matrix.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-STAKEHOLDER-IMPACT-001'));
      expect(contract.readAsStringSync(), contains('DIRECT_USERS'));
    });

    test('StakeholderImpactMatrixModel instantiates properly', () {
      const model = StakeholderImpactMatrixModel(
        caseVersionId: 'case-1',
        optionCode: 'OPT_A',
        netEquityScore: 3,
        impactItems: [
          StakeholderImpactItemModel(
            group: StakeholderGroupTypeModel.directUsers,
            impactType: StakeholderImpactTypeModel.benefit,
            impactScore: 4,
            description: 'Kullanım kolaylığı.',
          ),
          StakeholderImpactItemModel(
            group: StakeholderGroupTypeModel.workers,
            impactType: StakeholderImpactTypeModel.burden,
            impactScore: -1,
            description: 'Ek mesai.',
          ),
        ],
      );

      expect(model.netEquityScore, 3);
      expect(model.impactItems.length, 2);
    });

    test('InternalAlphaStrings contains Stakeholder Matrix localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.stakeholderMatrixEyebrow, contains('PAYDAŞ ETKİ'));
      expect(tr.stakeholderMatrixNetScore(3), contains('+3'));

      const en = KefeStrings(Locale('en'));
      expect(en.stakeholderMatrixEyebrow, contains('STAKEHOLDER IMPACT'));
      expect(en.stakeholderMatrixNetScore(3), contains('+3'));
    });
  });
}
