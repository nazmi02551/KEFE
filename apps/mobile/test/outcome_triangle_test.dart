import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/outcome_triangle_models.dart';

void main() {
  group('Outcome Triangle Tri-Axial Balance Engine (CAP-102)', () {
    test('ADR-0169 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0169-outcome-triangle-tri-axial-balance-engine.md');
      final contract = File('../../docs/contracts/outcome-triangle.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-OUTCOME-TRIANGLE-001'));
      expect(contract.readAsStringSync(), contains('RIGHTS_CENTRIC'));
    });

    test('OutcomeTriangleModel instantiates properly', () {
      const model = OutcomeTriangleModel(
        caseVersionId: 'case-1',
        optionCode: 'OPT_A',
        rulesWeight: 0.60,
        empathyWeight: 0.20,
        utilityWeight: 0.20,
        dominantArchetype: TriangleArchetypeModel.rightsCentric,
      );

      expect(model.dominantArchetype, TriangleArchetypeModel.rightsCentric);
      expect(model.rulesWeight, 0.60);
    });

    test('InternalAlphaStrings contains Triangle localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.triangleEyebrow, contains('ÜÇGENİ'));
      expect(tr.triangleArchetypeRights, contains('Kural'));

      const en = KefeStrings(Locale('en'));
      expect(en.triangleEyebrow, contains('TRIANGLE'));
      expect(en.triangleArchetypeRights, contains('Rights'));
    });
  });
}
