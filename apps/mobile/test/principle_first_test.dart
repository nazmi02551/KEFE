import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/principle_first_models.dart';

void main() {
  group('Principle-First Decision Flow Engine (CAP-006)', () {
    test('ADR-0187 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0187-principle-first-decision-flow.md');
      final contract = File('../../docs/contracts/principle-first-flow.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-PRINCIPLE-FIRST-001'));
      expect(contract.readAsStringSync(), contains('INDIVIDUAL_LIBERTY'));
    });

    test('PrincipleFirstModel instantiates properly', () {
      const model = PrincipleFirstModel(
        caseVersionId: 'case-1',
        primaryPrinciple: PrincipleTypeModel.individualLiberty,
        secondaryPrinciple: PrincipleTypeModel.proceduralJustice,
        consistencyScore: 0.88,
        reflectionPrompt: 'İlkesel tutarlılığınız korundu.',
      );

      expect(model.primaryPrinciple, PrincipleTypeModel.individualLiberty);
      expect(model.consistencyScore, 0.88);
    });

    test('InternalAlphaStrings contains Principle First localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.principleEyebrow, contains('İLKELER ÖNCELİKLİ'));
      expect(tr.principleTypeLiberty, contains('Bireysel Özgürlük'));

      const en = KefeStrings(Locale('en'));
      expect(en.principleEyebrow, contains('PRINCIPLE-FIRST'));
      expect(en.principleTypeLiberty, contains('Individual Liberty'));
    });
  });
}
