import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/vulnerable_groups_shield_models.dart';

void main() {
  group('Vulnerable Groups Protection Shield (CAP-026)', () {
    test('ADR-0185 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0185-vulnerable-groups-protection-shield.md');
      final contract = File('../../docs/contracts/vulnerable-groups-shield.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-VULNERABLE-SHIELD-001'));
      expect(contract.readAsStringSync(), contains('PERSONS_WITH_DISABILITIES'));
    });

    test('VulnerableGroupsShieldModel instantiates properly', () {
      const model = VulnerableGroupsShieldModel(
        caseVersionId: 'case-1',
        optionCode: 'OPT_A',
        overallProtectionStatus: ProtectionStatusModel.strongProtectiveFloor,
        safetyNetFloorScore: 0.85,
        cohortEvaluations: [
          CohortEvaluationItemModel(
            cohort: VulnerableCohortModel.personsWithDisabilities,
            impactScore: 0.80,
            assessment: 'Engelli erişilebilirliği tam sağlandı.',
          ),
        ],
      );

      expect(model.overallProtectionStatus, ProtectionStatusModel.strongProtectiveFloor);
      expect(model.safetyNetFloorScore, 0.85);
    });

    test('InternalAlphaStrings contains Vulnerable Groups localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.vulnerableEyebrow, contains('KIRILGAN GRUPLAR'));
      expect(tr.vulnerableCohortDisability, contains('Engelli'));

      const en = KefeStrings(Locale('en'));
      expect(en.vulnerableEyebrow, contains('VULNERABLE GROUPS'));
      expect(en.vulnerableCohortDisability, contains('Disabilities'));
    });
  });
}
