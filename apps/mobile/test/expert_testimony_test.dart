import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/expert_testimony_models.dart';

void main() {
  group('Expert Testimony & Institutional Endorsement (CAP-044)', () {
    test('ADR-0182 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0182-expert-testimony-and-institutional-endorsement-engine.md');
      final contract = File('../../docs/contracts/expert-institutional-testimony.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-EXPERT-TESTIMONY-001'));
      expect(contract.readAsStringSync(), contains('INDEPENDENT_ACADEMIC_EXPERT'));
    });

    test('ExpertTestimonyModel instantiates properly', () {
      const model = ExpertTestimonyModel(
        testimonyId: 'test-1',
        sourceName: 'Prof. Dr. Ayşe Yılmaz',
        archetype: TestimonyArchetypeModel.independentAcademicExpert,
        conflictOfInterestScore: 0.05,
        epistemicAuthorityTier: EpistemicAuthorityTierModel.highPeerReviewed,
        testimonyStatement: 'Akademik su havzası raporu.',
      );

      expect(model.archetype, TestimonyArchetypeModel.independentAcademicExpert);
      expect(model.epistemicAuthorityTier, EpistemicAuthorityTierModel.highPeerReviewed);
    });

    test('InternalAlphaStrings contains Expert Testimony localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.expertEyebrow, contains('EPİSTEMİK'));
      expect(tr.expertTierAcademic, contains('Bağımsız'));

      const en = KefeStrings(Locale('en'));
      expect(en.expertEyebrow, contains('EPISTEMIC'));
      expect(en.expertTierAcademic, contains('Peer-Reviewed'));
    });
  });
}
