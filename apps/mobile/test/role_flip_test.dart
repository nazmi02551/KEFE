import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/role_flip_models.dart';

void main() {
  group('Role Flip & Stakeholder Position Reweigh (CAP-007)', () {
    test('ADR-0188 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0188-role-flip-reweigh.md');
      final contract = File('../../docs/contracts/role-flip-reweigh.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-ROLE-FLIP-001'));
    });

    test('RoleFlipModel instantiates properly', () {
      const model = RoleFlipModel(
        caseVersionId: 'case-1',
        initialRole: 'Sanayici',
        flippedRole: 'Bölge Sakini',
        flippedScenarioPrompt: 'Nehir kenarında yaşayan bir köylü olduğunuzu hayal edin.',
        perspectiveShiftScore: 0.74,
      );

      expect(model.initialRole, 'Sanayici');
      expect(model.perspectiveShiftScore, 0.74);
    });

    test('InternalAlphaStrings contains Role Flip localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.roleFlipEyebrow, contains('ROL DEĞİŞİMİ'));
      expect(tr.roleFlipInitialLabel, contains('Başlangıç Bakış Açınız'));

      const en = KefeStrings(Locale('en'));
      expect(en.roleFlipEyebrow, contains('ROLE FLIP'));
      expect(en.roleFlipInitialLabel, contains('Your Initial Perspective'));
    });
  });
}
