import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/youth_deliberation_space_models.dart';

void main() {
  group('Youth & Student Deliberation Space (CAP-032)', () {
    test('ADR-0207 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0207-youth-deliberation-space.md');
      final contract = File('../../docs/contracts/youth-deliberation-space.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-YOUTH-SPACE-001'));
      expect(contract.readAsStringSync(), contains('CAMPUS_AND_EDUCATION_POLICY'));
    });

    test('YouthDeliberationSpaceModel instantiates properly', () {
      const model = YouthDeliberationSpaceModel(
        spaceId: 'spc_1',
        spaceName: 'ODTÜ Kampüs Ulaşımı',
        focusArea: YouthSpaceFocusAreaModel.campusAndEducationPolicy,
        institutionOrCommunity: 'ODTÜ',
        activeStudentCount: 350,
        consensusActionCount: 4,
      );

      expect(model.activeStudentCount, 350);
      expect(model.focusArea, YouthSpaceFocusAreaModel.campusAndEducationPolicy);
    });

    test('InternalAlphaStrings contains Youth Space localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.youthSpaceEyebrow, contains('GENÇLİK VE ÖĞRENCİ'));
      expect(tr.youthSpaceFocusCampus, contains('Kampüs'));

      const en = KefeStrings(Locale('en'));
      expect(en.youthSpaceEyebrow, contains('YOUTH & STUDENT'));
      expect(en.youthSpaceFocusCampus, contains('Campus'));
    });
  });
}
