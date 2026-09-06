import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/municipal_participatory_budgeting_models.dart';

void main() {
  group('Municipal & Participatory Budgeting (CAP-033)', () {
    test('ADR-0221 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0221-municipal-participatory-budgeting.md');
      final contract = File('../../docs/contracts/municipal-participatory-budgeting.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-MUN-BUDGET-001'));
      expect(contract.readAsStringSync(), contains('PARKS_AND_GREEN_SPACES'));
    });

    test('MunicipalBudgetProjectModel instantiates properly', () {
      const model = MunicipalBudgetProjectModel(
        projectId: 'prj_1',
        municipalityName: 'Kadıköy Belediyesi',
        projectDomain: MunicipalProjectDomainModel.parksAndGreenSpaces,
        requestedBudgetTry: 2500000,
        citizenVotesCount: 4500,
        civicApprovalRate: 0.90,
      );

      expect(model.requestedBudgetTry, 2500000);
      expect(model.civicApprovalRate, 0.90);
    });

    test('InternalAlphaStrings contains Municipal Budget localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.munBudEyebrow, contains('YEREL YÖNETİM'));
      expect(tr.munBudDomParks, contains('Parklar'));

      const en = KefeStrings(Locale('en'));
      expect(en.munBudEyebrow, contains('MUNICIPAL & PARTICIPATORY'));
      expect(en.munBudDomParks, contains('Parks'));
    });
  });
}
